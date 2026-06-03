from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from src.components.data_loader import DataLoader
from src.components.evaluation import Evaluator
from src.components.feature_engineering import FeatureEngineering
from src.components.scaling import FeatureScaler
from src.components.preprocessing import Preprocessor
from src.models.dbscan import DBSCAN
from src.models.isolation_forest import IsolationForest
from src.models.zscore import zscore


@dataclass(slots=True)
class AnalysisRequest:
    stock: str
    start_date: str
    end_date: str
    timeframe: str
    features: list[str]
    mode: str

    @classmethod
    def from_mapping(cls, config: dict[str, Any]) -> "AnalysisRequest":
        return cls(
            stock=config["stock"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            timeframe=config["timeframe"],
            features=list(config["features"]),
            mode=config["mode"],
        )


@dataclass(slots=True)
class PipelineResult:
    data: pd.DataFrame
    labels: dict[str, np.ndarray]
    metrics: dict[str, Any]
    best_params: dict[str, Any]
    model: Any = None

    def as_response(self, include_model: bool = False) -> dict[str, Any]:
        response = {
            "labels": self.labels,
            "metrics": self.metrics,
            "data": self.data,
        }
        if include_model:
            response["model"] = self.model
        return response


class AnomalyDetectorService:
    def predict(self, X: np.ndarray, df: pd.DataFrame, best_params: dict[str, Any]) -> dict[str, np.ndarray]:
        return {
            "dbscan": self._predict_dbscan(X, best_params.get("dbscan", {})),
            "isolation_forest": self._predict_isolation_forest(X, best_params.get("isolation_forest", {})),
            "zscore": self._predict_zscore(df, best_params.get("z_score", {}).get("threshold", 2.0)),
        }

    def _predict_dbscan(self, X: np.ndarray, params: dict[str, Any]) -> np.ndarray:
        model = DBSCAN(eps=params.get("eps", 1.0), min_pts=params.get("min_pts", 5))
        return model.fit_predict(X)

    def _predict_isolation_forest(self, X: np.ndarray, params: dict[str, Any]) -> np.ndarray:
        model = IsolationForest(
            n_trees=params.get("n_estimators", 100),
            contamination=params.get("contamination", 0.01),
        )
        return model.fit_predict(X)

    def _predict_zscore(self, df: pd.DataFrame, threshold: float) -> np.ndarray:
        if "returns" not in df.columns:
            if "close" not in df.columns:
                return np.ones(len(df), dtype=int)
            series = df["close"].ffill().fillna(0)
        else:
            series = df["returns"].fillna(0)

        z_scores = zscore(series)
        return np.where(np.abs(z_scores) > threshold, -1, 1)


class BaseAnalysisPipeline(ABC):
    def __init__(
        self,
        config: dict[str, Any] | AnalysisRequest,
        best_params: dict[str, Any],
        *,
        data_loader: DataLoader | None = None,
        preprocessor: Preprocessor | None = None,
        feature_engineer: FeatureEngineering | None = None,
        scaler: FeatureScaler | None = None,
        detector: AnomalyDetectorService | None = None,
    ) -> None:
        self.config = config if isinstance(config, AnalysisRequest) else AnalysisRequest.from_mapping(config)
        self.best_params = best_params or {}
        self.data_loader = data_loader or DataLoader()
        self.preprocessor = preprocessor or Preprocessor()
        self.feature_engineer = feature_engineer or FeatureEngineering()
        self.scaler = scaler or FeatureScaler()
        self.detector = detector or AnomalyDetectorService()

    def _prepare_features(self) -> pd.DataFrame:
        data = self.data_loader.load(self.config.stock, self.config.start_date, self.config.end_date)
        if data.empty:
            raise ValueError(f"No processed data found for {self.config.stock}")

        clean_data = self.preprocessor.transform(data, timeframe=self.config.timeframe)
        if clean_data.empty:
            raise ValueError("No data available after preprocessing")

        feature_df = self.feature_engineer.transform(clean_data, self.config.features)
        if feature_df.empty:
            raise ValueError("Feature engineering produced an empty dataset")

        return feature_df

    def _build_metrics(self, feature_df: pd.DataFrame, label_sets: dict[str, np.ndarray]) -> dict[str, Any]:
        evaluator = Evaluator()
        return {
            "dbscan": evaluator.compute(feature_df, label_sets["dbscan"]),
            "isolation_forest": evaluator.compute(feature_df, label_sets["isolation_forest"]),
            "zscore": evaluator.compute(feature_df, label_sets["zscore"]),
        }

    def _attach_labels(self, feature_df: pd.DataFrame, label_sets: dict[str, np.ndarray]) -> pd.DataFrame:
        result_df = feature_df.copy()
        result_df["cluster_dbscan"] = label_sets["dbscan"]
        result_df["cluster_isolation_forest"] = label_sets["isolation_forest"]
        result_df["cluster_zscore"] = label_sets["zscore"]
        result_df["cluster"] = label_sets["dbscan"]
        return result_df

    @abstractmethod
    def run(self) -> PipelineResult:
        raise NotImplementedError


class StaticAnalysisPipeline(BaseAnalysisPipeline):
    def run(self) -> PipelineResult:
        feature_df = self._prepare_features()
        X_scaled = self.scaler.fit_transform(feature_df, self.config.features)
        label_sets = self.detector.predict(X_scaled, feature_df, self.best_params)
        metrics = self._build_metrics(feature_df, label_sets)
        result_df = self._attach_labels(feature_df, label_sets)
        return PipelineResult(data=result_df, labels=label_sets, metrics=metrics, best_params=self.best_params)

    def __init__(self, config: dict[str, Any] | AnalysisRequest, best_params: dict[str, Any], window_size: int = 500, **kwargs: Any) -> None:
        super().__init__(config, best_params, **kwargs)
        self.window_size = window_size

    def run(self) -> PipelineResult:
        feature_df = self._prepare_features()

        if feature_df.empty:
            raise ValueError("Feature engineering produced an empty dataset")

        warmup = min(max(100, self.window_size), len(feature_df))

        dbscan_labels = pd.Series(1, index=feature_df.index, dtype=int)
        iso_labels = pd.Series(1, index=feature_df.index, dtype=int)
        zscore_labels = pd.Series(1, index=feature_df.index, dtype=int)

        for index in range(max(warmup - 1, 0), len(feature_df)):
            window_df = feature_df.iloc[: index + 1].tail(self.window_size)
            X_scaled = self.scaler.fit_transform(window_df, self.config.features)
            window_label_sets = self.detector.predict(X_scaled, window_df, self.best_params)

            dbscan_labels.iloc[index] = int(window_label_sets["dbscan"][-1])
            iso_labels.iloc[index] = int(window_label_sets["isolation_forest"][-1])
            zscore_labels.iloc[index] = int(window_label_sets["zscore"][-1])

        result_df = feature_df.copy()
        result_df["cluster_dbscan"] = dbscan_labels
        result_df["cluster_isolation_forest"] = iso_labels
        result_df["cluster_zscore"] = zscore_labels

        combined = pd.Series(1, index=feature_df.index, dtype=int)
        combined[(dbscan_labels == -1) | (iso_labels == -1) | (zscore_labels == -1)] = -1

        result_df["cluster"] = combined
        result_df["anomaly"] = result_df["cluster"] == -1

        evaluator = Evaluator()
        metrics = {
            "dbscan": evaluator.compute(result_df, result_df["cluster_dbscan"]),
            "isolation_forest": evaluator.compute(result_df, result_df["cluster_isolation_forest"]),
            "zscore": evaluator.compute(result_df, result_df["cluster_zscore"]),
            "combined": evaluator.compute(result_df, result_df["cluster"]),
        }

        labels = {
            "dbscan": dbscan_labels.to_numpy(),
            "isolation_forest": iso_labels.to_numpy(),
            "zscore": zscore_labels.to_numpy(),
            "combined": combined.to_numpy(),
        }

        return PipelineResult(
            data=result_df,
            labels=labels,
            metrics=metrics,
            best_params=self.best_params,
        )
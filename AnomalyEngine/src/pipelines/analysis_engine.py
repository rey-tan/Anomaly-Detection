from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd
from src.components.data_loader import DataLoader
from src.components.evaluation import Evaluator
from src.components.feature_engineering import FeatureEngineering
from src.components.scaling import FeatureScaler
from src.components.preprocessing import Preprocessor
from src.models.dbscan import DBSCAN
from src.models.isolation_forest import IsolationForest
from src.models.zscore import zscore
from src.utils.load import load_config
from src.utils.paths import CONFIG


@dataclass(slots=True)
class AnalysisRequest:
    stock: str
    start_date: str
    end_date: str
    timeframe: str
    algorithm: str
    features: Optional[list[str]] = None

    @classmethod
    def from_mapping(cls, config: dict[str, Any]) -> "AnalysisRequest":
        return cls(
            stock=config["stock"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            timeframe=config["timeframe"],
            algorithm = config["algorithm"],
            features = load_config(CONFIG / "config.yaml").get("features", [])
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
    def predict(self, X: np.ndarray, df: pd.DataFrame, best_params: dict[str, Any], algorithm: str = "ensemble") -> dict[str, np.ndarray]:

        result = {}

        z_labels,z_scores = self._predict_zscore(df, best_params.get("z_score", {}).get("threshold", 3.0))

        result["z_score_label"] = z_labels
        result["z_score"] = z_scores

        if algorithm == "ensemble" :
            db_labels = self._predict_dbscan(X, best_params.get("dbscan", {}))
            if_labels, if_scores = self._predict_isolation_forest(X, best_params.get("isolation_forest", {}))

            result["dbscan_label"] = db_labels
            result["isolation_forest_label"] = if_labels
            result["isolation_forest_score"] = if_scores

        elif algorithm == "dbscan":
            db_labels = self._predict_dbscan(X, best_params.get("dbscan", {}))  

            result["dbscan_label"] = db_labels

        elif algorithm == "isolation_forest":
            if_labels, if_scores = self._predict_isolation_forest(X, best_params.get("isolation_forest", {}))

            result["isolation_forest_label"] = if_labels
            result["isolation_forest_score"] = if_scores


        return result
    
      

    def _predict_dbscan(self, X: np.ndarray, params: dict[str, Any]) -> np.ndarray:
        model = DBSCAN(eps=params.get("eps", 1.0), min_pts=params.get("min_pts", 5))
        return model.fit_predict(X)

    def _predict_isolation_forest(self, X: np.ndarray, params: dict[str, Any]) -> np.ndarray:
        model = IsolationForest(
            n_trees=params.get("n_estimators", 100),
            contamination=params.get("contamination", 0.01),
        )
        labels = model.fit_predict(X)
        # compute anomaly scores per sample (higher = more anomalous)
        try:
            scores = model.anomaly_score(X)
        except Exception:
            scores = None
        return labels, scores

    def _predict_zscore(self, df: pd.DataFrame, threshold: float) -> np.ndarray:
        if "returns" not in df.columns:
            if "close" not in df.columns:
                return np.ones(len(df), dtype=int)
            series = df["close"].ffill().fillna(0)
        else:
            series = df["returns"].fillna(0)

        z_scores = zscore(series)
        labels = np.where(np.abs(z_scores) > threshold, -1, 1)

        return labels,z_scores


class AnalysisEngine:
    def __init__(
        self,
        config: dict[str, Any] | AnalysisRequest,
        best_params: dict[str, Any]
    ) -> None:
        self.config = config if isinstance(config, AnalysisRequest) else AnalysisRequest.from_mapping(config)
        self.best_params = best_params or {}
        self.data_loader = DataLoader()
        self.preprocessor = Preprocessor()
        self.feature_engineer = FeatureEngineering()
        self.scaler = FeatureScaler()
        self.detector = AnomalyDetectorService()

    def _prepare_features(self) -> pd.DataFrame:
        data = self.data_loader.load(self.config.stock, self.config.start_date, self.config.end_date)

        if data.empty:
            raise ValueError(f"No processed data found for {self.config.stock}")

        clean_data = self.preprocessor.transform(data, timeframe=self.config.timeframe)

        if clean_data.empty:
            raise ValueError("No data available after preprocessing")
       
        if not self.config.features:
            raise ValueError("No features configured for analysis")
        
        feature_df = self.feature_engineer.transform(clean_data, self.config.features)
        if feature_df.empty:
            raise ValueError("Feature engineering produced an empty dataset")

        return feature_df

    def _build_metrics(self, feature_df: pd.DataFrame, label_sets: dict[str, np.ndarray]) -> dict[str, Any]:
        evaluator = Evaluator()

        metrics = {
            "z_score": evaluator.compute(feature_df, label_sets["z_score_label"])
        }
    
        if self.config.algorithm == "isolation_forest":
            metrics["isolation_forest"] = evaluator.compute(feature_df, label_sets["isolation_forest_label"])
        elif self.config.algorithm == "dbscan":
            metrics["dbscan"] = evaluator.compute(feature_df, label_sets["dbscan_label"])
        elif self.config.algorithm == "ensemble":
            metrics["dbscan"] = evaluator.compute(feature_df, label_sets["dbscan_label"])
            metrics["isolation_forest"] = evaluator.compute(feature_df, label_sets["isolation_forest_label"])
        else:
            raise ValueError(f"Unknown algorithm specified: {self.config.algorithm}")
        
        return metrics
       

    def _attach_labels(self, feature_df: pd.DataFrame, label_sets: dict[str, np.ndarray]) -> pd.DataFrame:
        result_df = feature_df.copy()

        result_df["z_score"] = label_sets["z_score"]
        result_df["z_score_label"] = label_sets["z_score_label"]

        if self.config.algorithm == "isolation_forest":
            result_df["isolation_forest_label"] = label_sets["isolation_forest_label"]
            result_df["isolation_forest_score"] = label_sets["isolation_forest_score"]

        elif self.config.algorithm == "dbscan":
            result_df["dbscan_label"] = label_sets["dbscan_label"]

        elif self.config.algorithm == "ensemble":
            result_df["dbscan_label"] = label_sets["dbscan_label"]
            result_df["isolation_forest_label"] = label_sets["isolation_forest_label"]
            result_df["isolation_forest_score"] = label_sets["isolation_forest_score"]

        else:
            raise ValueError(f"Unknown algorithm specified: {self.config.algorithm}")
        
        return result_df


    def run(self) -> PipelineResult:
        feature_df = self._prepare_features()
        X_scaled = self.scaler.fit_transform(feature_df, self.config.features)
        label_sets = self.detector.predict(X_scaled, feature_df, self.best_params,self.config.algorithm)
        metrics = self._build_metrics(feature_df, label_sets)
        result_df = self._attach_labels(feature_df, label_sets)
        return PipelineResult(data=result_df, labels=label_sets, metrics=metrics, best_params=self.best_params)


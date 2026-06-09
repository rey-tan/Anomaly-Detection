import numpy as np
from src.models.dbscan import DBSCAN
from src.models.isolation_forest import IsolationForest
from src.models.zscore import zscore


class AnomalyDetector:
    
    def fit(self, X, model_type: str = "isolation_forest", **kwargs):
        self._model = self.train_model(X, model_type=model_type, **kwargs)
        return self._model

    def predict(self, X):
        if hasattr(self, "_model") and hasattr(self._model, "predict"):
            return self._model.predict(X)
        raise RuntimeError("Model not trained or predict not available on model")
    

    def _predict_dbscan(self,X, params):
        model = DBSCAN(eps=params.get("eps", 1.0), min_pts=params.get("min_pts", 5))
        return model.fit_predict(X)


    def _predict_isolation_forest(self,X, params):
        model = IsolationForest(
            n_trees=params.get("n_estimators", 100),
            contamination=params.get("contamination", 0.01),
        )
        return model.fit_predict(X)


    def _predict_zscore(self,df, threshold: float):
        if "returns" not in df.columns:
            if "close" not in df.columns:
                return np.ones(len(df), dtype=int)
            series = df["close"].ffill().fillna(0)
        else:
            series = df["returns"].fillna(0)

        z_scores = zscore(series)
        return np.where(np.abs(z_scores) > threshold, -1, 1)


    def train_model(self,X, best_params, df):
        return {
            "dbscan": self._predict_dbscan(X, best_params.get("dbscan", {})),
            "isolation_forest": self._predict_isolation_forest(X, best_params.get("isolation_forest", {})),
            "zscore": self._predict_zscore(df, best_params.get("z_score", {}).get("threshold", 3.0)),
        }


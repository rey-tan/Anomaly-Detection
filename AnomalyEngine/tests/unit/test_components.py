import pandas as pd
import numpy as np

from src.components.preprocessing import Preprocessor
from src.components.feature_engineering import FeatureEngineering
from src.components.scaling import FeatureScaler
from src.components.evaluation import Evaluator
from src.components.anomaly_detection import AnomalyDetector


def test_preprocessor_empty_input():
    pre = Preprocessor()
    df = pd.DataFrame()

    out = pre.transform(df, timeframe="1D")

    assert out.empty or out is None


def test_evaluator_compute_metrics():
    df = pd.DataFrame({
        "volatility": [0.1, 0.2, 0.3, 0.4],
        "volume": [10, 20, 30, 40],
    })
    labels = np.array([1, -1, 1, -1])
    ev = Evaluator()
    res = ev.compute(df, labels)
    assert "anomaly_rate" in res
    assert res["n_noise"] == 2


def test_train_model_basic_outputs():
    # small synthetic X and df
    X = np.vstack([np.linspace(0, 1, 10), np.linspace(0, 1, 10)]).T
    df = pd.DataFrame({"close": np.linspace(0, 1, 10)})
    detector = AnomalyDetector()
    out = detector.train_model(X, {}, df)
    assert set(out.keys()) == {"dbscan", "isolation_forest", "zscore"}
    assert len(out["dbscan"]) == 10


    







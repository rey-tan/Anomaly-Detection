import pandas as pd
import numpy as np

from src.components.preprocessing import Preprocessor
from src.components.feature_engineering import FeatureEngineering
from src.components.scaling import FeatureScaler
from src.components.evaluation import Evaluator
from src.components.anomaly_detection import train_model


def test_preprocessor_resamples_and_shapes():
    # create minute-level data across 3 days
    rng = pd.date_range("2023-01-01", periods=60 * 24 * 3, freq="T")
    df = pd.DataFrame({
        "transaction_time": rng,
        "price": np.random.rand(len(rng)) * 100,
        "volume": np.random.randint(1, 1000, size=len(rng)),
    })

    pre = Preprocessor()
    out = pre.transform(df, timeframe="1D")

    # should have OHLCV and non-empty
    assert not out.empty
    assert set(["open", "high", "low", "close", "volume"]).issubset(out.columns)


def test_feature_engineering_adds_indicators():
    n = 100
    dates = pd.date_range(end=pd.Timestamp.today(), periods=n)
    df = pd.DataFrame({"close": np.cumsum(np.random.randn(n)) + 100, "volume": np.random.randint(1,100,size=n)}, index=dates)

    fe = FeatureEngineering()
    out = fe.transform(df.copy(), features=["close"])

    # indicators present
    assert "SMA_10" in out.columns
    assert "RSI" in out.columns
    assert "Upper_BB" in out.columns


def test_feature_scaler_returns_array_shape():
    n = 50
    df = pd.DataFrame({"a": np.arange(n), "b": np.arange(n) * 2.0})
    scaler = FeatureScaler()
    X = scaler.fit_transform(df, ["a", "b"]) 
    assert X.shape == (n, 2)


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
    out = train_model(X, {}, df)
    assert set(out.keys()) == {"dbscan", "isolation_forest", "zscore"}
    assert len(out["dbscan"]) == 10

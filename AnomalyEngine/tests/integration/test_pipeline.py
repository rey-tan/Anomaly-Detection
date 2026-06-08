import pandas as pd
import numpy as np

from src.pipelines.analysis_engine import AnalysisEngine, AnomalyDetectorService
from src.components.preprocessing import Preprocessor
from src.components.feature_engineering import FeatureEngineering
from src.components.scaling import FeatureScaler


def make_mock_data(n=200):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=n, freq='D')
    df = pd.DataFrame({
        'open': np.linspace(10, 20, n), #creates a linearly increasing open price from 10 to 20 with evenly spaced values over n days
        'high': np.linspace(10.5, 20.5, n),
        'low': np.linspace(9.5, 19.5, n),
        'close': np.linspace(10, 20, n),
        'volume': np.random.randint(1, 1000, size=n), #generates random integer values between 1 and 1000 for the volume column, with a total of n values
    }, index=dates)
    return df


class MockLoader:
    def __init__(self, df):
        self.df = df

    def load(self, stock, start_date, end_date):
        return self.df


def test_static_pipeline_basic_run():
    df = make_mock_data()
    loader = MockLoader(df)
    config = {
        'stock': 'MOCK',
        'start_date': str(df.index[0].date()),
        'end_date': str(df.index[-1].date()),
        'timeframe': '1D',
    }

    engine = AnalysisEngine(config, best_params={}, data_loader=loader)
    res = engine.run()

    assert res.data is not None
    assert 'dbscan' in res.metrics
    assert 'zscore' in res.metrics


def test_anomaly_detector_service_predicts_labels():
    df = make_mock_data(n=150)
    detector = AnomalyDetectorService()
    X = np.vstack([np.linspace(0, 1, len(df)), np.linspace(1, 2, len(df))]).T

    labels = detector.predict(X, df, {})

    assert set(labels.keys()) == {'dbscan', 'isolation_forest', 'isolation_forest_score', 'zscore'}
    assert len(labels['dbscan']) == len(df)
    assert len(labels['zscore']) == len(df)





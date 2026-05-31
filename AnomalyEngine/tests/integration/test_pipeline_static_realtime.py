import pandas as pd
import numpy as np

from src.pipelines.analysis_engine import StaticAnalysisPipeline, RealtimeAnalysisPipeline
from src.components.preprocessing import Preprocessor
from src.components.feature_engineering import FeatureEngineering
from src.components.scaling import FeatureScaler
from src.pipelines.analysis_engine import AnomalyDetectorService


def make_mock_data(n=200):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=n, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'open': np.linspace(10, 20, n),
        'high': np.linspace(10.5, 20.5, n),
        'low': np.linspace(9.5, 19.5, n),
        'close': np.linspace(10, 20, n),
        'volume': np.random.randint(1, 1000, size=n),
    })
    df = df.set_index('date')
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
        'features': ['close', 'volume'],
        'mode': 'static',
    }

    pipeline = StaticAnalysisPipeline(config, best_params={}, data_loader=loader)
    res = pipeline.run()
    assert res.data is not None
    assert 'dbscan' in res.metrics


def test_realtime_pipeline_runs_and_returns_labels():
    df = make_mock_data(n=150)
    loader = MockLoader(df)
    config = {
        'stock': 'MOCK',
        'start_date': str(df.index[0].date()),
        'end_date': str(df.index[-1].date()),
        'timeframe': '1D',
        'features': ['close', 'volume'],
        'mode': 'realtime',
    }

    pipeline = RealtimeAnalysisPipeline(config, best_params={}, data_loader=loader)
    res = pipeline.run()
    assert 'dbscan' in res.metrics
    assert hasattr(res, 'data')

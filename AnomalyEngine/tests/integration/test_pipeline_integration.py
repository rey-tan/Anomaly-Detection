import pandas as pd
import numpy as np

from src.pipelines.analysis_engine import StaticAnalysisPipeline
from src.components.feature_engineering import FeatureEngineering
from src.components.scaling import FeatureScaler
from src.pipelines.analysis_engine import AnomalyDetectorService
from src.components.preprocessing import Preprocessor


def test_static_pipeline_runs_with_mocked_loader():
    # Create synthetic raw data with transaction_time, price and volume
    dates = pd.date_range(end=pd.Timestamp.today(), periods=120, freq='D')
    df = pd.DataFrame({
        'transaction_time': dates,
        'price': (np.cumsum(np.random.randn(len(dates))) + 100),
        'volume': np.random.randint(1, 1000, size=len(dates)),
    })

    class MockLoader:
        def load(self, stock, start_date, end_date):
            return df

    config = {
        'stock': 'TEST',
        'start_date': str(dates[0].date()),
        'end_date': str(dates[-1].date()),
        'timeframe': '1D',
        'features': ['close'],
        'mode': 'static'
    }

    pipeline = StaticAnalysisPipeline(
        config,
        best_params={},
        data_loader=MockLoader(),
        preprocessor=Preprocessor(),
        feature_engineer=FeatureEngineering(),
        scaler=FeatureScaler(),
        detector=AnomalyDetectorService(),
    )

    result = pipeline.run()
    assert hasattr(result, 'metrics')
    assert 'dbscan' in result.metrics
    assert not result.data.empty

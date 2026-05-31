import pandas as pd
from src.models.zscore import zscore


def test_zscore_zero_std_returns_zeros():
    s = pd.Series([5.0] * 10)
    zs = zscore(s)
    assert (zs == 0).all()


def test_zscore_standardizes_nontrivial_series():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    zs = zscore(s)
    assert abs(zs.mean()) < 1e-8
    assert abs(zs.std(ddof=0) - 1.0) < 1e-8

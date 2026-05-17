import pandas as pd

def zscore(series):
    mean = series.mean()
    std = series.std(ddof=0)  # for population std deviation degrees of freedom is ero

    # avoid division by zero by returning all zeroes
    if std == 0:
        return pd.Series([0] * len(series), index=series.index)

    z = (series - mean) / std
    return z
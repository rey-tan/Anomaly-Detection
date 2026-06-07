import pandas as pd

class Preprocessor:
    """Object-oriented preprocessing service.

    Use `Preprocessor().transform(df, timeframe)` to get the same result as
    `preprocess(df, timeframe)`.
    """
    def transform(self, df: pd.DataFrame, timeframe: str = "1D") -> pd.DataFrame:
        df = df.copy()

        if df.empty:
            return df

        #resample if needed
        df = df.resample(timeframe).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )

        # Filter dataframe
        df = df.drop_duplicates()
        df = df.dropna()

        return df


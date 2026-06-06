import pandas as pd

class Preprocessor:
    """Object-oriented preprocessing service.

    Use `Preprocessor().transform(df, timeframe)` to get the same result as
    `preprocess(df, timeframe)`.
    """
    def transform(self, df: pd.DataFrame, timeframe: str = "1D") -> pd.DataFrame:
        df = df.copy()

        # Ensure a datetime index for resampling
        if not isinstance(df.index, pd.DatetimeIndex):
            datetime_column = None
            for candidate in ("date", "transaction_time", "timestamp", "time"):
                if candidate in df.columns:
                    datetime_column = candidate
                    break

            if datetime_column is None:
                df.index = pd.to_datetime(df.index, errors="coerce")
            else:
                df[datetime_column] = pd.to_datetime(df[datetime_column], errors="coerce")
                df = df.set_index(datetime_column)

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have a DatetimeIndex or a valid datetime column for resampling.")

        # Normalize pricing columns for OHLCV aggregation
        if "open" not in df.columns and "price" in df.columns:
            df["open"] = df["price"]
        if "high" not in df.columns and "price" in df.columns:
            df["high"] = df["price"]
        if "low" not in df.columns and "price" in df.columns:
            df["low"] = df["price"]
        if "close" not in df.columns and "price" in df.columns:
            df["close"] = df["price"]

        agg_dict = {}
        if "open" in df.columns:
            agg_dict["open"] = ("open", "first")
        if "high" in df.columns:
            agg_dict["high"] = ("high", "max")
        if "low" in df.columns:
            agg_dict["low"] = ("low", "min")
        if "close" in df.columns:
            agg_dict["close"] = ("close", "last")
        if "volume" in df.columns:
            agg_dict["volume"] = ("volume", "sum")

        # Preserve other columns by taking the last available value in each resample window
        for column in df.columns:
            if column not in agg_dict and column not in ("open", "high", "low", "close", "volume"):
                agg_dict[column] = (column, "last")

        df = df.resample(timeframe).agg(agg_dict)

        df = df.drop_duplicates()
        df = df.dropna()

        return df


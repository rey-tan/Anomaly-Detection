import pandas as pd
import numpy as np




class FeatureEngineering:
    """Class-based feature engineering service.

    Provides `transform(df, features)` which mirrors `build_features(df, features)` behavior.
    """
    def __init__(self, sma_windows=(10,20,50), rsi_period=14, vol_window=20):
        self.sma_windows = sma_windows
        self.rsi_period = rsi_period
        self.vol_window = vol_window

    def transform(self,df:pd.DataFrame,features:list)->pd.DataFrame :
        df = df.copy()
        # Compute features
        df["returns"] = df["close"].pct_change()
        df["close"] = df["close"].replace(0, np.nan)
        df["volatility"] = df["returns"].rolling(window=20).std()


        #Calculate additional features

        # 1. Calculate Simple moving averages of last N days
        df["SMA_10"] = df["close"].rolling(window=10).mean()
        df["SMA_20"] = df["close"].rolling(window=20).mean()
        df["SMA_50"] = df["close"].rolling(window=50).mean()


        # 2. Calculate Relative Strength Index
        def calculate_rsi(data, periods=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        df["RSI"] = calculate_rsi(df["close"])


        # 3. Calculate Boilinger bands
        df["Upper_BB"] = df["SMA_20"] + (df["close"].rolling(window=20).std() * 2)
        df["Lower_BB"] = df["SMA_20"] - (df["close"].rolling(window=20).std() * 2)

        df["bb_width"] = (df["Upper_BB"] - df["Lower_BB"]) / df["close"]

         # convert every value in features columns to numeric value
        df[features] = df[features].apply(
            pd.to_numeric, errors="coerce"
        )  

        # replace infinite values with nan and drop them
        df.replace(
            [np.inf, -np.inf], np.nan, inplace=True
        )  
        df = df.dropna(subset=features) 

        # print(df.tail())

        return df

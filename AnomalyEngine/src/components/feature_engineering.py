import pandas as pd
import numpy as np

def build_features(df:pd.DataFrame,features:list)->pd.DataFrame :

    df = df.copy()
    # Compute features
    df["returns"] = df["close"].pct_change()
    df["close"] = df["close"].replace(0, np.nan)
    df["volatility"] = df["returns"].rolling(window=20).std()


    # convert every value in features columns to numeric value
    df[features] = df[features].apply(
        pd.to_numeric, errors="coerce"
    )  

    # replace infinite values with nan and drop them
    df.replace(
        [np.inf, -np.inf], np.nan, inplace=True
    )  
    df = df.dropna(subset=features) 



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

    # print(df.tail())


    return df
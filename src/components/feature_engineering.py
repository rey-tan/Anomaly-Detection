import pandas as pd
import numpy as np

def build_features(df:pd.Dataframe,features:list):
    # Compute features
    df["returns"] = df["close"].pct_change()
    df["close"] = df["close"].replace(0, np.nan)
    df["volatility"] = df["returns"].rolling(window=20).std()



    print(df[["close", "volume", "returns", "volatility"]].isna().sum())


    df[features] = df[features].apply(
        pd.to_numeric, errors="coerce"
    )  
    # converts every value in features columns to numeric value
    df.replace(
        [np.inf, -np.inf], np.nan, inplace=True
    )  
    # replace inf and -inf 

    df = df.dropna(subset=features)  # drops rows where any of the features are NaN
    # print(df[["close", "volume", "returns", "volatility"]].isna().sum())


    return df
import pandas as pd

def preprocess(df: pd.DataFrame,timeframe="1D") -> pd.DataFrame:

    df = df.copy()

    
    df["date"] = pd.to_datetime(df["transaction_time"])
    df = df.set_index("date").sort_index()

    # drop unnecessary columns
    df = df.drop(columns=["transaction_time"], errors="ignore")


    #resample if needed
    df = df.resample(timeframe).agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        volume=("volume", "sum"),
    )

    # Filter dataframe
    df = df.drop_duplicates()

    return df


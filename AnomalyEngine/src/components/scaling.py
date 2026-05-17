from sklearn.preprocessing import StandardScaler
import pandas as pd

def scale_features(df:pd.DataFrame, features:list[str]):
    scaler = StandardScaler()

    X = scaler.fit_transform(df[features])

    return X
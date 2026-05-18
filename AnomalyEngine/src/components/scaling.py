from sklearn.preprocessing import StandardScaler
import pandas as pd

def scale_features(df:pd.DataFrame, features:list[str]):
    scaler = StandardScaler()

    X = scaler.fit_transform(df[features])

    return X


class FeatureScaler:
    """Class-based feature scaler service.

    Use `FeatureScaler().fit_transform(df, features)` to scale features.
    """
    def __init__(self) -> None:
        self.scaler = StandardScaler()

    def fit_transform(self, df: pd.DataFrame, features: list[str]):
        return self.scaler.fit_transform(df[features])
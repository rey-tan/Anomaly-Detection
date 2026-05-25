from sklearn.preprocessing import RobustScaler
import pandas as pd


class FeatureScaler:
    """Class-based feature scaler service.

    Use `FeatureScaler().fit_transform(df, features)` to scale features.
    """
    def __init__(self) -> None:
        self.scaler = RobustScaler()

    def fit_transform(self, df: pd.DataFrame, features: list[str]):
        scaler = RobustScaler()

        X = scaler.fit_transform(df[features])

        return X
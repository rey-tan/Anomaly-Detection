from src.components.data_loader import load_data
from src.components.preprocessing import preprocess
from src.components.feature_engineering import build_features
from src.components.scaling import scale_features
from src.components.anomaly_detection import train_model
from src.components.evaluation import compute_anomaly_stats
import pandas as pd

WINDOW = 500  # last 500 rows


def get_window(df):
    return df.tail(WINDOW)


def detect_anomaly(df, features, best_params):
    window_df = get_window(df)
    X_scaled = scale_features(window_df, features)
    model, labels = train_model(X_scaled, best_params)
    window_df = window_df.copy()
    window_df["cluster"] = labels
    return window_df, model


def streaming_simulation(df, features, best_params):
    df = df.copy()
    labels = pd.Series(0, index=df.index, dtype=int)
    last_model = None

    for i in range(100, len(df)):
        current_df = df.iloc[: i + 1].copy()
        window_df, model = detect_anomaly(current_df, features, best_params)
        labels.iloc[i] = int(window_df["cluster"].iloc[-1])
        last_model = model

    df["cluster"] = labels
    df["anomaly"] = df["cluster"] == -1
    return df, last_model


def run_realtime_pipeline(config, best_params):
    data = load_data(
        symbol=config["stock"],
        start_date=config["start_date"],
        end_date=config["end_date"]
    )
    features = config["features"]

    clean_data = preprocess(data, timeframe=config["timeframe"])
    feature_df = build_features(clean_data, features)

    result_df, model = streaming_simulation(feature_df, features, best_params)
    metrics = compute_anomaly_stats(result_df, result_df["cluster"])

    return {
        "model": model,
        "labels": result_df["cluster"],
        "metrics": metrics,
        "data": result_df,
    }


    
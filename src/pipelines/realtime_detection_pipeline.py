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

    X_scaled = scale_features(window_df,features)

    model,labels = train_model(X_scaled,best_params) #retrain on window

    window_df["cluster"]=labels

    return window_df


def streaming_simulation(df,features,best_params):
    results = []

    for i in range(100, len(df)):
        #get the first i rows
        current_df = df.iloc[:i].copy()
        
        window_df = detect_anomaly(current_df, features, best_params)
        
        latest = window_df.iloc[-1]
        
        results.append({
            "time": latest.name,
            "close": latest["close"],
            "anomaly": latest["anomaly"]
        })

    return pd.DataFrame(results)


def run_realtime_pipeline(config,best_params):

    data = load_data(
        symbol=config["stock"],
        start_date=config["start_date"],
        end_date=config["end_date"]
    )
    features = config["features"]

    clean_data = preprocess(data,timeframe=config["timeframe"])

    feature_df = build_features(clean_data,features)

    results = streaming_simulation(feature_df,features,best_params)
    

    return results;


    
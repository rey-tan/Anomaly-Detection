from src.components.data_loader import load_data
from src.components.preprocessing import preprocess
from src.components.feature_engineering import build_features
from src.components.scaling import scale_features
from src.components.anomaly_detection import train_model
from src.components.evaluation import compute_anomaly_stats



def run_pipeline(config,best_params):

    data = load_data(
        symbol=config["stock"],
        start_date=config["start_date"],
        end_date=config["end_date"]
    )
    features = config["features"]

    clean_data = preprocess(data,timeframe=config["timeframe"])

    feature_df = build_features(clean_data,features)

    X_scaled = scale_features(feature_df,features)

    model,labels = train_model(X_scaled,best_params)

    metrics = compute_anomaly_stats(feature_df,labels)

    feature_df["cluster"]=labels

    print(feature_df["cluster"].value_counts())
    return {
        "model":model,
        "labels":labels,
        "metrics":metrics,
        "data":feature_df
    }


    


    
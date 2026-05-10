from components.data_loader import load_data
from components.preprocessing import preprocess
from components.feature_engineering import build_features
from components.scaling import scale_features
from components.anomaly_detection import train_model
from components.evaluation import evaluate_model
from src.utils.load import load_config,load_json
from src.utils.paths import CONFIG,ARTIFACTS



def run_pipeline():
    config = load_config(CONFIG / "config.yaml")
    best_params = load_json(ARTIFACTS / "best_params.json")

    data = load_data(
        stock=config["stock"],
        start=config["start_date"],
        end=config["end_date"]
    )
    features = config["features"]

    clean_data = preprocess(data)

    feature_df = build_features(clean_data,features)

    X_scaled = scale_features(feature_df,features)

    model,labels = train_model(X_scaled,best_params)

    evaluate_model(labels, features)

    return model,labels


    


    
from src.components.data_loader import load_data
from src.components.preprocessing import preprocess
from src.components.feature_engineering import build_features
from src.components.scaling import scale_features
from src.components.anomaly_detection import train_model
from src.components.evaluation import compute_anomaly_stats


def run_pipeline(config,best_params):

    try:
        data = load_data(
            symbol=config["stock"],
            start_date=config["start_date"],
            end_date=config["end_date"]
        )
        features = config["features"]

        clean_data = preprocess(data,timeframe=config["timeframe"])

        feature_df = build_features(clean_data,features)

        X_scaled = scale_features(feature_df,features)

        label_sets = train_model(X_scaled,best_params, feature_df)

        metrics = {
            "dbscan": compute_anomaly_stats(feature_df, label_sets["dbscan"]),
            "isolation_forest": compute_anomaly_stats(feature_df, label_sets["isolation_forest"]),
            "zscore": compute_anomaly_stats(feature_df, label_sets["zscore"]),
        }

        feature_df["cluster_dbscan"] = label_sets["dbscan"]
        feature_df["cluster_isolation_forest"] = label_sets["isolation_forest"]
        feature_df["cluster_zscore"] = label_sets["zscore"]
        feature_df["cluster"] = label_sets["dbscan"]

        return {
            "labels": label_sets,
            "metrics": metrics,
            "data": feature_df
        }
    except KeyError as e:
        st.error(f"Missing config key: {e}")

    except ValueError as e:
        st.error(f"Value error: {e}")

    except Exception as e:
        st.exception(e) 

    return None
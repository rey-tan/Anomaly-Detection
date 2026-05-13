from src.models.dbscan import DBSCAN
from src.utils.paths import CONFIG

def train_model(X,best_params):
    
    dbscan_params = best_params['dbscan']

    model = DBSCAN(eps=dbscan_params['eps'], min_pts=dbscan_params['min_pts'])

    labels = model.fit_predict(X);

    return model,labels


    # Ensemble: flag if ANY model agrees
# anomaly_score = (z_score_pred + dbscan_pred + if_pred) / 3

# # High confidence anomaly: if 2/3 models agree
# high_confidence = anomaly_score >= 0.66

# # Or: take union of all predictions (sensitive, catch more)
# any_anomaly = (z_score_pred | dbscan_pred | if_pred)

# # Or: take intersection (conservative, fewer false positives)
# consensus_anomaly = (z_score_pred & dbscan_pred & if_pred)
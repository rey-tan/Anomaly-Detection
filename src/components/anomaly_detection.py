from models.dbscan import DBSCAN
import json
from src.utils.paths import CONFIG

def train_model(X,best_params):
    
    dbscan_params = best_params['dbscan']

    model = DBSCAN(eps=dbscan_params['eps'], min_pts=dbscan_params['min_pts'])

    labels = model.fit_predict(X);

    return model,labels
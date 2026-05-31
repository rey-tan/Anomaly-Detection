import numpy as np
from src.models.dbscan import DBSCAN


def test_dbscan_two_clusters_and_noise():
    # two tight clusters and one distant noise point
    cluster1 = np.array([[0, 0], [0.1, 0], [0, 0.1]])
    cluster2 = np.array([[5, 5], [5.1, 5], [5, 5.1]])
    noise = np.array([[20, 20]])

    X = np.vstack([cluster1, cluster2, noise])

    model = DBSCAN(eps=0.5, min_pts=2)
    labels = model.fit_predict(X)

    # expect at least one noise point labeled -1
    assert -1 in labels
    # expect at least two different cluster ids (excluding noise)
    cluster_ids = set([l for l in labels if l != -1])
    assert len(cluster_ids) >= 2

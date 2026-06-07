import numpy as np
from src.models.isolation_forest import IsolationForest


def test_isolation_forest_detects_outlier():
    # create a simple 2D cloud plus a far outlier
    rng = np.random.default_rng(0)
    normal = rng.normal(loc=0.0, scale=0.5, size=(100, 2)) #with mean 0 and std 0.5
    outlier = np.array([[10.0, 10.0]])
    X = np.vstack([normal, outlier])

    model = IsolationForest(n_trees=20, contamination=0.01, random_state=0, max_samples=50)
    labels = model.fit_predict(X)

    # outlier should be labeled -1
    assert labels[-1] == -1
    # most points should be labeled normal (1)
    assert (labels == 1).sum() >= 90

def test_isolation_forest_no_outliers():
    rng = np.random.default_rng(0)
    X = rng.normal(0, 0.5, size=(100, 2))

    model = IsolationForest(
        n_trees=20,
        contamination=0.01,
        random_state=0,
        max_samples=50
    )

    labels = model.fit_predict(X)

    # should not flag many anomalies
    assert (labels == -1).sum() <= 2
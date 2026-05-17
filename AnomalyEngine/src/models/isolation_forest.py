import numpy as np


class IsolationForest:
    def __init__(self, n_trees=50, contamination=0.02, random_state=42,max_samples=256):
        self.n_trees = n_trees
        self.contamination = contamination
        self.trees = []
        self.threshold = None
        self.max_samples = max_samples
        self.random_state = random_state
        self.rng = np.random.default_rng(random_state)

    def fit(self, X):
        self.trees = []

        size = min(self.max_samples, len(X))
        self.max_depth = int(np.ceil(np.log2(size)))

        # Build trees
        for _ in range(self.n_trees):
            idx = self.rng.choice(
                len(X), size=size, replace=False
            )
            X_sample = X[idx]
            tree = self._build_tree(X_sample, depth=0)
            self.trees.append(tree)

        # Compute anomaly scores on training data
        train_scores = self.anomaly_score(X)

        # MORE score = more anomalous → use high percentile as the threshold

        # self.threshold = np.percentile(train_scores, p)

        self.threshold = np.percentile(train_scores, 100 * (1 - self.contamination))

        # so what we are doing here is finding the value below which p% of the data lies,

        # i.e if contamination = 0.02 then threshold = 98% percentile of the scores
        # so anomalies are above 98th percentile ,then 98% of the values are below it

        return self

    def _build_tree(self, X, depth):
        if depth >= self.max_depth or len(X) <= 1:
            return {"size": len(X)}

        feature = self.rng.integers(X.shape[1])

        min_val = X[:, feature].min()
        max_val = X[:, feature].max()

        if min_val == max_val:
            return {"size": len(X)}

        split = self.rng.uniform(min_val, max_val)

        left = X[X[:, feature] < split]
        right = X[X[:, feature] >= split]

        return {
            "feature": feature,
            "split": split,
            "left": self._build_tree(left, depth + 1),
            "right": self._build_tree(right, depth + 1),
        }

    def _path_length(self, x, node, depth=0):
        if "size" in node:
            return depth

        if x[node["feature"]] < node["split"]:
            return self._path_length(x, node["left"], depth + 1)
        else:
            return self._path_length(x, node["right"], depth + 1)

    def anomaly_score(self, X):
        scores = []
        for x in X:
            path_lengths = [self._path_length(x, tree) for tree in self.trees]
            scores.append(np.mean(path_lengths))
        scores = np.array(scores)

        # this is calculating the average path_length it took to isolate a point. the faster a point is isolated, more anomalous it is. so less score => anomaly

        return -scores
        # so higher the score more anomalous it is

    def decision_function(self, X):
        scores = self.anomaly_score(X)
        return scores - self.threshold

    def predict(self, X):
        scores = self.decision_function(X)
        return np.where(scores > 0, -1, 1)


    def fit_predict(self, X):
        self.fit(X)
        return self.predict(X)

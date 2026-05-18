def compute_anomaly_stats(df, labels):
    results = {}

    # 1. anomaly ratio
    results["anomaly_rate"] = (labels == -1).mean()

    # 2. cluster stats
    results["n_noise"] = sum(labels == -1)
    results["n_clusters"] = len(set(labels)) - (1 if -1 in labels else 0)

    # 3. feature behavior check
    anomaly_df = df[labels == -1]
    normal_df = df[labels != -1]

    results["volatility_anomaly_mean"] = anomaly_df["volatility"].mean()
    results["volatility_normal_mean"] = normal_df["volatility"].mean()

    results["volume_anomaly_mean"] = anomaly_df["volume"].mean()
    results["volume_normal_mean"] = normal_df["volume"].mean()

    return results


class Evaluator:
    """Object-oriented evaluation service providing anomaly statistics."""

    def compute(self, df, labels):
        return compute_anomaly_stats(df, labels)
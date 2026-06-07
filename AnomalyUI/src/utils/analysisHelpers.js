import { fetchAnalysisData } from "../api";

export function extractMetricsAndParams(data) {
  if (!data) return { metrics: {}, bestParams: {} };

  // If using new format with models
  if (data.models) {
    const metrics = {};
    const bestParams = {};
    Object.entries(data.models).forEach(([modelName, modelResult]) => {
      if (modelResult.metrics) metrics[modelName] = modelResult.metrics;
      if (modelResult.params) {
        const paramKey = modelName === "zscore" ? "z_score" : modelName;
        bestParams[paramKey] = modelResult.params;
      }
    });
    return { metrics, bestParams };
  }

  // Fallback to old format
  return {
    metrics: data.metrics || {},
    bestParams: data.best_params || {},
  };
}

export function isAnomalyRow(row) {
  return (
    row.cluster === -1 ||
    row.anomaly === true ||
    row.cluster_dbscan === -1 ||
    row.cluster_isolation_forest === -1
  );
}

export function countAnomalyRows(data) {
  if (!Array.isArray(data)) return 0;
  return data.filter(isAnomalyRow).length;
}

export function deriveAnomalyCount(metrics, dataLength = 0) {
  if (!metrics || typeof metrics !== "object") return null;
  if (typeof metrics.anomaly_count === "number") {
    return metrics.anomaly_count;
  }
  if (typeof metrics.n_noise === "number") {
    return metrics.n_noise;
  }
  if (typeof metrics.anomaly_rate === "number" && dataLength > 0) {
    return Math.round(metrics.anomaly_rate * dataLength);
  }
  return null;
}

export async function enrichAnalysisWithAnomalyCount(analysis, token, fallbackData = null) {
  if (!analysis) return analysis;
  let anomalyCount = null;
  if (Array.isArray(fallbackData)) {
    anomalyCount = countAnomalyRows(fallbackData);
  }
  if (anomalyCount === null) {
    anomalyCount = deriveAnomalyCount(analysis.metrics, Array.isArray(analysis.data) ? analysis.data.length : 0);
  }
  if (anomalyCount === null && analysis.id && token) {
    try {
      const payload = await fetchAnalysisData(token, analysis.id);
      anomalyCount = countAnomalyRows(payload.data || []);
    } catch (err) {
      anomalyCount = 0;
    }
  }
  return { ...analysis, anomalyCount: anomalyCount ?? 0 };
}

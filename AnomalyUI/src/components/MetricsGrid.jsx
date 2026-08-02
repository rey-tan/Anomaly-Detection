import React from 'react'

function MetricCard({ title, value, description }) {
  return (
    <div className="metric-card">
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-description">{description}</div>
    </div>
  );
}

function formatParamValue(val) {
  if (typeof val === "number") {
    return Number.isInteger(val) ? val : val.toFixed(2);
  }
  if (Array.isArray(val) || typeof val === "object") {
    return JSON.stringify(val);
  }
  return String(val);
}

export default function MetricsGrid({ results = {}, data = {}, handleToggleFavorite = null }) {
  const metricEntries = Object.entries(results || {}).filter(([model]) => model.toLowerCase() !== "z_score");
  let ensemble = false;
  let criticalPoints = [];
  let densityPoints = [];
  let structurePoints = [];

  if (metricEntries.length === 2) {
    ensemble = true;

    criticalPoints = data.filter(
      row => row.dbscan_label === -1 &&
        row.isolation_forest_label === -1
    );

    densityPoints = data.filter(
      row => row.dbscan_label === -1 &&
        row.isolation_forest_label !== -1
    );

    structurePoints = data.filter(
      row => row.isolation_forest_label === -1 &&
        row.dbscan_label !== -1
    );
  }

  return (
    <div className="metrics-wrapper">
      <div className="section-heading compact results-title">
        <div style={{ width: "100%" }}>
          <h2>Analysis feedback</h2>
          <p>Review model metrics, event counts, and tuning parameters.</p>
        </div>

      </div>
      <div className="detector-summary">
        {ensemble && (
          <div className="detector-summary-card">
            <strong>Ensemble Results</strong>
            <small>{criticalPoints.length} critical anomalies</small>
            <small>{densityPoints.length} density anomalies</small>
            <small>{structurePoints.length} structural anomalies</small>
          </div>
        )}
        {metricEntries.map(([model, modelData]) => (
          <div className="detector-summary-card" key={model}>
            <strong>{model.replace(/_/g, " ")}</strong>
            <span>{((modelData.metrics?.anomaly_rate ?? 0) * 100).toFixed(1)}% anomalies</span>
            <small>
              {modelData.metrics?.n_noise ?? 0} flagged points
              {modelData.metrics?.anomaly_rate === 0 ? " · no anomalies detected with current params" : ""}
            </small>
          </div>
        ))}
      </div>
      <div className="metric-grid">
        {console.log("Rendering MetricsGrid with entries:", metricEntries)}
        {metricEntries.map(([model, modelData]) => {
          const { metrics, params } = modelData || {};

          return (
            <div className="analysis-block" key={model}>
              <h3>{model.replace(/_/g, " ")}</h3>
              <div className="metric-grid-inner">
                <MetricCard
                  title="Anomaly rate"
                  value={`${((metrics?.anomaly_rate ?? 0) * 100).toFixed(1)}%`}
                  description="Percent of points flagged as anomalies"
                />
                <MetricCard
                  title="Anomaly count"
                  value={`${metrics?.n_noise ?? 0}`}
                  description="Total outlier observations"
                />
                <MetricCard
                  title="Tuning parameters"
                  description={
                    Object.keys(params || {}).length > 0 ? (
                      <div className="metric-params-list">
                        {Object.entries(params).map(([key, val]) => (
                          <div key={key}>{key}: {formatParamValue(val)}</div>
                        ))}
                      </div>
                    ) : (
                      "—"
                    )
                  }
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

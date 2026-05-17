function MetricCard({ title, value, description }) {
  return (
    <div className="metric-card">
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-description">{description}</div>
    </div>
  );
}

export default function MetricsGrid({ metrics = {}, bestParams = {} }) {
  const metricEntries = Object.entries(metrics || {});
  return (
    <div className="metrics-wrapper">
      <div className="section-heading">
        <div>
          <h2>Analysis feedback</h2>
          <p>Review model metrics, event counts, and tuning parameters.</p>
        </div>
      </div>
      <div className="metric-grid">
        {metricEntries.map(([model, summary]) => (
          <div className="analysis-block" key={model}>
            <h3>{model.replace(/_/g, " ")}</h3>
            <div className="metric-grid-inner">
              <MetricCard
                title={`${((summary.anomaly_rate ?? 0) * 100).toFixed(1)}%`}
                value="Anomaly rate"
                description="Percent of points flagged as anomalies"
              />
              <MetricCard
                title={`${summary.n_noise ?? 0}`}
                value="Anomaly count"
                description="Total outlier observations"
              />
              <MetricCard
                title={`${summary.n_clusters ?? 0}`}
                value="Clusters"
                description="Unique normal clusters detected"
              />
            </div>
          </div>
        ))}
      </div>
      {bestParams && Object.keys(bestParams).length > 0 ? (
        <div className="best-params-card">
          <h3>Tuned parameters</h3>
          <pre>{JSON.stringify(bestParams, null, 2)}</pre>
        </div>
      ) : null}
    </div>
  );
}

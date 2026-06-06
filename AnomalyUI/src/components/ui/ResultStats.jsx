import React from 'react'
export default function ResultStats({ data = [] }) {
  const anomalyCount = data.filter((row) => (
    row.cluster === -1 || row.anomaly === true || row.cluster_dbscan === -1 || row.cluster_isolation_forest === -1
  )).length;
  const points = data.length;

  const formatDate = (value) => (value ? String(value).split("T")[0] : "—");

  const firstDate = formatDate(data[0]?.date || data[0]?.transaction_time);
  const lastDate = formatDate(data[data.length - 1]?.date || data[data.length - 1]?.transaction_time);

  return (
    <div className="result-summary">
      <div className="summary-card">
        <span>Data points</span>
        <strong>{points}</strong>
      </div>
      <div className="summary-card">
        <span>Anomalies flagged</span>
        <strong>{anomalyCount}</strong>
      </div>
      <div className="summary-card">
        <span>Analysis window</span>
        <strong>
          {firstDate} → {lastDate}
        </strong>
      </div>
    </div>
  )
}

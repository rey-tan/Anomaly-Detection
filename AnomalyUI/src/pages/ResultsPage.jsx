import React from 'react'
import AnomalyChart from '../components/AnomalyChart'
import MetricsGrid from '../components/MetricsGrid'
import AnalysisHistory from '../components/AnalysisHistory'
import { toggleFavorite } from '../api'
import ExplainAnalysis from './ExplainAnalysis'


export default function ResultsPage({
  token,
  results,
  selectedAnalysis,
  setResults,
  setSelectedAnalysis,
  handleSelectAnalysis,
  navigate,
}) {
  const handleToggleFavorite = async () => {
    if (!selectedAnalysis) return;

    try {
      const updated = await toggleFavorite(token, selectedAnalysis.id, !selectedAnalysis.is_favorite);
      setSelectedAnalysis(updated);
      try { window.dispatchEvent(new CustomEvent('favorites:changed')); } catch (e) { }
    } catch (err) {
      console.error(err);
    }
  };

  const dataRows = Array.isArray(results?.data) ? results.data : [];
  const flaggedCount = dataRows.filter((r) => r.cluster === -1 || r.anomaly === true || r.cluster_dbscan === -1 || r.cluster_isolation_forest === -1).length;

  const rsiValues = dataRows.map((r) => r.RSI ?? r.rsi).filter((v) => Number.isFinite(Number(v))).map(Number);
  const avgRsi = rsiValues.length ? rsiValues.reduce((a, b) => a + b, 0) / rsiValues.length : null;
  const bbValues = dataRows.map((r) => r.bb_width ?? r.BB_width ?? r.bbWidth).filter((v) => Number.isFinite(Number(v))).map(Number);
  const avgBb = bbValues.length ? bbValues.reduce((a, b) => a + b, 0) / bbValues.length : null;


  return (
    <section className="page-split results-layout">
      <div className="page-panel">
        <div className="page-intro">
          <p className="eyebrow">Results</p>
          <h2>Inspect the latest analysis outputs</h2>
          <p>Chart, metrics, and tuned parameters:</p>

        </div>

        {results ?
          <div className="result-summary">
            <div className="summary-card">
              <span>Data points</span>
              <strong>{(results.data || []).length}</strong>
            </div>
            <div className="summary-card">
              <span>Anomalies flagged</span>
              <strong>{flaggedCount}</strong>
            </div>
            <div className="summary-card">
              <span>Avg RSI</span>
              <strong>{avgRsi != null ? Number(avgRsi).toFixed(2) : '—'}</strong>
            </div>
            <div className="summary-card">
              <span>Avg BB width</span>
              <strong>{avgBb != null ? Number(avgBb).toFixed(2) : '—'}</strong>
            </div>
          </div>

          : null}
        {results ?
          <MetricsGrid results={results.models} selectedAnalysis={selectedAnalysis} handleToggleFavorite={handleToggleFavorite} /> : 
            <section className="empty-state-card">
              <h2>No results yet</h2>
              <p>Run an analysis from the Analysis page to populate this view.</p>
            </section>}
        <div className="analysis-footer">
            <ExplainAnalysis token={token} results ={results} selectedAnalysis={selectedAnalysis} flaggedCount={flaggedCount}/>
        </div>
        <AnalysisHistory token={token} onSelectAnalysis={handleSelectAnalysis} />
      </div>

      <div className="page-panel">
        {results ? <AnomalyChart data={results.data || []} /> : <section className="empty-state-card"><h2>Chart preview</h2><p>Once analysis is complete, price action and anomaly markers appear here.</p></section>}
      </div>
    </section>
  )
}

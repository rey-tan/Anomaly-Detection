import React from 'react'
import AnomalyChart from '../components/AnomalyChart'
import MetricsGrid from '../components/MetricsGrid'
import AnalysisHistory from '../components/AnalysisHistory'
import { toggleFavorite } from '../api'


export default function ResultsPage({
  token,
  results,
  selectedAnalysis,
  setResults,
  setSelectedAnalysis,
  aiExplanation,
  aiExplanationEntries,
  aiError,
  aiLoading,
  handleExplainWithAI,
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

  const flaggedCount = (results?.data || []).filter((r) => r.cluster === -1 || r.anomaly === true || r.cluster_dbscan === -1 || r.cluster_isolation_forest === -1).length;


  return (
    <section className="page-split results-layout">
      <div className="page-panel">
        <div className="page-intro">
          <p className="eyebrow">Results page</p>
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
          </div>

          : null}
        {results ?
          <MetricsGrid results={results.models} selectedAnalysis={selectedAnalysis} handleToggleFavorite={handleToggleFavorite} /> : 
            <section className="empty-state-card">
              <h2>No results yet</h2>
              <p>Run an analysis from the Analysis page to populate this view.</p>
            </section>}
        <div className="analysis-footer">
          <div className="ai-explanation-section">
            {results ? (
              <div className="results-ai-actions">
                <button className="primary-button" type="button" onClick={handleExplainWithAI} disabled={aiLoading || !flaggedCount}>
                  {aiLoading ? 'Analyzing with AI…' : 'Analyze with AI'}
                </button>
                <span className="results-ai-note">{flaggedCount ? `${flaggedCount} flagged points available for explanation` : 'No flagged points to explain'}</span>
              </div>
            ) : null}
            {aiError ? <div className="alert-box">{aiError}</div> : null}
            {aiExplanation ? (
              <section className="dashboard-card results-ai-card">
                <div className="section-heading compact">
                  <div>
                    <p className="eyebrow">AI explanation</p>
                    <h3>Why these points were flagged</h3>
                    <p>Generated from the latest analyzed result set.</p>
                  </div>
                  <div className="results-ai-source">Source: {aiExplanation.source}</div>
                </div>
                {aiExplanationEntries.length ? (
                  <div className="results-ai-grid">
                    {aiExplanationEntries.map((entry) => (
                      <article key={`${entry.date}-${entry.rowNumber}`} className="results-ai-card-item">
                        <div className="results-ai-card-header">
                          <span className="results-ai-card-label">{entry.date}</span>
                          <strong>{`Row ${entry.rowNumber}`}</strong>
                        </div>
                        <ul className="results-ai-card-bullets">
                          {entry.bullets.map((bullet, bulletIndex) => (
                            <li key={bulletIndex}>{bullet}</li>
                          ))}
                        </ul>
                        {entry.summary ? <p className="results-ai-card-summary">{entry.summary}</p> : null}
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="results-ai-summary">{aiExplanation.summary}</p>
                )}
              </section>
            ) : null}
          </div>
        </div>
        <AnalysisHistory token={token} onSelect={(payload, analysis) => { setResults(payload); setSelectedAnalysis(analysis); navigate('/results'); }} />
      </div>

      <div className="page-panel">
        {results ? <AnomalyChart data={results.data || []} /> : <section className="empty-state-card"><h2>Chart preview</h2><p>Once analysis is complete, price action and anomaly markers appear here.</p></section>}
      </div>
    </section>
  )
}

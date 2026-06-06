import React from 'react'
import AnalysisPanel from '../components/AnalysisPanel'

export default function AnalysisPage({ onSubmit, loading, error }) {
  return (
    <section className="page-split">
      <div className="page-panel">
        <div className="page-intro">
          <p className="eyebrow">Analysis:</p>
          <h2>Run a new anomaly detection job</h2>
        </div>
        <AnalysisPanel onSubmit={onSubmit} loading={loading} />
        {error ? <div className="alert-box">{error}</div> : null}
      </div>

      <aside className="page-panel page-panel-aside">
        <div className="page-intro compact-copy">
          <p className="eyebrow">Before you run</p>
          <h3>Keep the set small and intentional</h3>
          <p>Choose the symbol, window, and features you actually want to inspect. You can move to the results page after the run completes.</p>
        </div>

        <img src="/abstract-stock-market.webp" alt="Abstract illustration of stock market analysis" className="aside-graphic" />
      </aside>
    </section>
  )
}

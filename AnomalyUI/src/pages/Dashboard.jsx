import React from 'react'
import { useNavigate } from 'react-router-dom'
import FavoritesPanel from '../components/FavoritesPanel'

export default function DashboardPage({ user, lastConfig, results, onOpenLastRun }) {
  const navigate = useNavigate();
  const lastAnalysis = lastConfig?.config || lastConfig || {};
  const stock = lastAnalysis?.stock || lastAnalysis?.symbol;
  const timeframe = lastAnalysis?.timeframe;
  const startDate = lastAnalysis?.start_date || lastAnalysis?.startDate;
  const endDate = lastAnalysis?.end_date || lastAnalysis?.endDate;
  const mode = lastAnalysis?.mode;
  const featureCount = lastAnalysis?.features?.length || 0;
  const anomalyCount = results?.data?.filter((r) => r.cluster === -1 || r.anomaly === true || r.cluster_dbscan === -1 || r.cluster_isolation_forest === -1).length || 0;
  const activeMetricCount = Object.keys(results?.models || {}).length;
  const isAdmin = user?.role === 'admin';
  return (
    <>
      <section className="hero-card hero-card-split">
        <div>
          <p className="eyebrow">Live insights</p>
          <h2>Overview of the current anomaly workspace</h2>
          <p>Track model health, see the last analyzed symbol, and move into a dedicated page for the next task.</p>
        </div>
        <div className="hero-footer">
          <span>{user?.role ? `Role: ${user.role}` : "Analyst dashboard"}</span>
          <strong>Backend API: {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}</strong>
        </div>
      </section>

      <section className="stats-grid">
        <article className="stat-card"><span>Current page</span><h3>Dashboard</h3><p>Use the sidebar to switch to analysis, results, or admin pages.</p></article>
        <article className="stat-card"><span>Latest symbol</span><h3>{lastConfig?.stock || '—'}</h3><p>Most recent analysis target.</p></article>
        <article className="stat-card"><span>Flagged anomalies</span><h3>{anomalyCount}</h3><p>Count from the latest result set.</p></article>
        <article className="stat-card"><span>Metrics groups</span><h3>{activeMetricCount}</h3><p>How many models are currently summarized.</p></article>
      </section>

      <section className="dashboard-grid">
        <article className="dashboard-card">
          <div className="section-heading compact">
            <div>
              <h2>Quick actions</h2>
              <p>Open a focused page for the task you want to complete next.</p>
            </div>
          </div>
          <div className="quick-links">
            <button className="quick-link" onClick={() => navigate('/analysis')} type="button">Run a new analysis</button>
            <button className="quick-link" onClick={() => navigate('/results')} type="button" disabled={!results}>Review latest results</button>
            {isAdmin && (
              <>
                <button className="quick-link" onClick={() => navigate('/data')} type="button">Manage data</button>
                <button className="quick-link" onClick={() => navigate('/users')} type="button">Manage users</button>
              </>
            )}
          </div>
        </article>

        <article className="dashboard-card">
          <div className="section-heading compact">
            <div>
              <h2>Latest Analysis</h2>
              <p><span onClick={onOpenLastRun} className="highlighted-text">Visit</span> the most recent saved analysis, including historical runs from earlier sessions.</p>
            </div>
          </div>
          <div className="context-stack">
            <div className="context-row"><span>Stock</span><strong>{stock || '—'}</strong></div>
            <div className="context-row"><span>Window</span><strong>{startDate && endDate ? `${startDate} – ${endDate}` : '—'}</strong></div>
            <div className="context-row"><span>Timeframe</span><strong>{timeframe || '—'}</strong></div>
            <div className="context-row"><span>Feature count</span><strong>{featureCount}</strong></div>
          </div>
          {/* <div className="card-actions">
            <button className="primary-button last-run-button" type="button" onClick={onOpenLastRun} disabled={!stock}>
              Open last run
            </button>
          </div> */}
        </article>
      
      <FavoritesPanel token={localStorage.getItem('anomalyui_token') || ''} onSelect={onOpenLastRun} />

      </section>

    </>
  )
}

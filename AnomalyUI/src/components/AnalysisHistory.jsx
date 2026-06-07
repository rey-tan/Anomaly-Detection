import React from "react";
import { useEffect, useState } from "react";
import { fetchAnalyses, toggleFavorite } from "../api";

export default function AnalysisHistory({ token, onSelectAnalysis }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetchAnalyses(token)
      .then((list) => setItems(list || []))
      .catch((err) => setError(err.message || "Could not load analyses"))
      .finally(() => setLoading(false));
  }, [token]);

  const handleClick = async (analysis) => {
    if (!onSelectAnalysis) return;
    onSelectAnalysis(analysis.id);
  };

  const handleFavorite = async (analysis, ev) => {
    ev.stopPropagation();
    try {
      const updated = await toggleFavorite(token, analysis.id, !analysis.is_favorite);
      setItems((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      try {
        window.dispatchEvent(new CustomEvent("favorites:changed"));
      } catch (e) {}
    } catch (err) {
      setError(err.message || "Failed to update favorite");
    }
  };

  return (
    <aside className="history-panel analysis-history-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Past analyses</p>
          <h3>Quickly revisit prior runs</h3>
          <p>Click an entry to load its results into the viewer, or star it to mark it as a favorite.</p>
        </div>
      </div>
      {loading ? <div className="loading">Loading…</div> : null}
      {error ? <div className="alert-box">{error}</div> : null}
      <div className="analysis-list">
        {items.map((a) => (
          <article key={a.id} className={a.is_favorite ? "analysis-list-item favorite" : "analysis-list-item"} >
            <div className="analysis-entry">
              <div className="analysis-row">
                <strong>{a.stock}</strong>
                <small>{new Date(a.executed_at).toLocaleString()}</small>
              </div>
              <div className="analysis-meta">
                <span>{a.mode}</span>
                <span>{a.timeframe}</span>
                <span>{a.status}</span>
              </div>
            </div>
            <div className="button-row">
 <button className="favorite-button view-button" type="button" onClick={() => handleClick(a)}>View</button>
            <button className="favorite-button" type="button" onClick={(ev) => handleFavorite(a, ev)} aria-label="Toggle favorite">
              {a.is_favorite ? "★ Favorite" : "☆ Favorite"}
            </button>
            </div>
           
          </article>
        ))}
      </div>
    </aside>
  );
}

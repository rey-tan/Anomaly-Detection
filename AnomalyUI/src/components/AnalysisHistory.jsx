import { useEffect, useState } from "react";
import { fetchAnalyses, fetchAnalysisData, toggleFavorite } from "../api";

export default function AnalysisHistory({ token, onSelect }) {
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
    try {
      const payload = await fetchAnalysisData(token, analysis.id);
      onSelect(payload, analysis);
    } catch (err) {
      setError(err.message || "Failed to load artifact");
    }
  };

  const handleFavorite = async (analysis, ev) => {
    ev.stopPropagation();
    try {
      const updated = await toggleFavorite(token, analysis.id, !analysis.is_favorite);
      setItems((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch (err) {
      setError(err.message || "Failed to update favorite");
    }
  };

  return (
    <aside className="history-panel">
      <div className="section-heading compact">
        <div>
          <h3>Past analyses</h3>
          <p>Click an entry to load its results into the viewer.</p>
        </div>
      </div>
      {loading ? <div className="loading">Loading…</div> : null}
      {error ? <div className="alert-box">{error}</div> : null}
      <ul className="analysis-list">
        {items.map((a) => (
          <li key={a.id} className="analysis-list-item">
            <button type="button" onClick={() => handleClick(a)}>
              <div className="analysis-row">
                <strong>{a.stock}</strong>
                <small>{new Date(a.executed_at).toLocaleString()}</small>
              </div>
              <div className="analysis-meta">
                <span>{a.mode}</span>
                <span>{a.timeframe}</span>
                <span>{a.status}</span>
              </div>
            </button>
            <button className="favorite-button" onClick={(ev) => handleFavorite(a, ev)}>
              {a.is_favorite ? "★" : "☆"}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

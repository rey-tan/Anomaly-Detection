import { useEffect, useState } from "react";
import { fetchAnalyses, fetchAnalysisData, toggleFavorite } from "../api";

export default function FavoritesPanel({ token, onSelect }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetchAnalyses(token)
      .then((list) => setItems((list || []).filter((a) => a.is_favorite)))
      .catch((err) => setError(err.message || "Could not load favorites"))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    if (!token) return;
    const handler = () => {
      setLoading(true);
      fetchAnalyses(token)
        .then((list) => setItems((list || []).filter((a) => a.is_favorite)))
        .catch((err) => setError(err.message || "Could not load favorites"))
        .finally(() => setLoading(false));
    };
    window.addEventListener("favorites:changed", handler);
    return () => window.removeEventListener("favorites:changed", handler);
  }, [token]);

  const handleClick = async (analysis) => {
    try {
      const payload = await fetchAnalysisData(token, analysis.id);
      onSelect(payload, analysis);
    } catch (err) {
      setError(err.message || "Failed to load artifact");
    }
  };

  const handleToggle = async (analysis, ev) => {
    ev && ev.stopPropagation();
    try {
      const updated = await toggleFavorite(token, analysis.id, !analysis.is_favorite);
      setItems((prev) => prev.filter((p) => p.id !== updated.id));
      // notify others that favorites changed
      try {
        window.dispatchEvent(new CustomEvent("favorites:changed"));
      } catch (e) {}
    } catch (err) {
      setError(err.message || "Failed to update favorite");
    }
  };

  return (
    <div className="side-rail-card favorites-panel">
      <p className="eyebrow">Favorites</p>
      <h3>Starred analyses</h3>
      <p className="hint">Quick access to analyses you've marked important.</p>
      {loading ? <div className="loading">Loading…</div> : null}
      {error ? <div className="alert-box">{error}</div> : null}
      <div className="favorites-list">
        {items.length === 0 ? (
          <p className="muted">No favorites yet — star an analysis to save it here.</p>
        ) : (
          items.map((a) => (
            <div key={a.id} className="favorite-item">
              <button className="analysis-entry small" onClick={() => handleClick(a)} type="button">
                <strong>{a.stock}</strong>
                <small>{new Date(a.executed_at).toLocaleDateString()}</small>
              </button>
              <button className="favorite-button" onClick={(ev) => handleToggle(a, ev)} aria-label="Remove favorite">
                Remove
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

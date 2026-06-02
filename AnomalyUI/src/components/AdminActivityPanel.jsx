import { useEffect, useState } from "react";
import { fetchUserActivity } from "../api";

export default function AdminActivityPanel({ token, userId, onClose }) {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || !userId) return;
    let active = true;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await fetchUserActivity(token, userId);
        if (active) setActivities(data || []);
      } catch (err) {
        if (active) setError(err.message || "Failed to load activity");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [token, userId]);

  return (
    <aside className="activity-panel">
      <div className="activity-header">
        <h3>User activity</h3>
        <button className="text-button" onClick={onClose}>Close</button>
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      {loading ? <div>Loading…</div> : null}
      <div className="activity-list">
        {activities.map((a) => (
          <div key={a.id} className="activity-row">
            <div className="activity-meta">
              <div className="activity-action">{a.action}</div>
              <div className="activity-date">{a.created_at ? String(a.created_at).split("T")[0] : ""}</div>
            </div>
            <div className="activity-details">{a.details ? JSON.stringify(a.details) : null}</div>
          </div>
        ))}
      </div>
    </aside>
  );
}

import { useEffect, useState } from "react";
import { fetchUserActivity, getUsers } from "../api";

export default function ActivityPage({ token, initialUserId, onBack }) {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(initialUserId || "");
  const [query, setQuery] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let active = true;
    const loadUsers = async () => {
      try {
        const u = await getUsers(token);
        if (active) setUsers(u || []);
      } catch (err) {
        console.error(err);
      }
    };
    loadUsers();
    return () => { active = false; };
  }, [token]);

  useEffect(() => {
    if (!token || !selectedUser) {
      setActivities([]);
      return;
    }
    let active = true;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await fetchUserActivity(token, selectedUser);
        if (active) setActivities(data || []);
      } catch (err) {
        if (active) setError(err.message || "Failed to load activity");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, [token, selectedUser]);

  return (
    <section className="page-split single-column">
      <div className="page-panel">
        <div className="page-intro">
          <p className="eyebrow">Activity</p>
          <h2>Audit log</h2>
          <p>Filter by user to inspect recent actions.</p>
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
          <select value={selectedUser} onChange={(e) => { setSelectedUser(e.target.value); setPage(1); }} className="admin-select">
            <option value="">Select a user</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.username}</option>
            ))}
          </select>
          <input placeholder="Search actions/details" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} className="admin-input" style={{ width: 220 }} />
          <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }} className="admin-input" />
          <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }} className="admin-input" />
          <button className="text-button" onClick={() => { setPage(1); }} type="button">Apply</button>
          <button className="text-button" onClick={onBack} type="button">Back</button>
          <button className="text-button" onClick={() => {
            const filtered = activities.filter((a) => {
              const q = query.toLowerCase();
              const inAction = a.action && a.action.toLowerCase().includes(q);
              const inDetails = a.details && JSON.stringify(a.details).toLowerCase().includes(q);
              return (!query || inAction || inDetails) &&
                (!startDate || (a.created_at && String(a.created_at).split('T')[0] >= startDate)) &&
                (!endDate || (a.created_at && String(a.created_at).split('T')[0] <= endDate));
            });
            const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${selectedUser || 'activity'}-export.json`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
          }} type="button">Export JSON</button>
        </div>

        {error ? <div className="form-error">{error}</div> : null}
        {loading ? <div>Loading…</div> : null}

        <div className="admin-list">
          {(() => {
            const filtered = activities.filter((a) => {
              const q = query.toLowerCase();
              const inAction = a.action && a.action.toLowerCase().includes(q);
              const inDetails = a.details && JSON.stringify(a.details).toLowerCase().includes(q);
              const afterStart = !startDate || (a.created_at && String(a.created_at).split('T')[0] >= startDate);
              const beforeEnd = !endDate || (a.created_at && String(a.created_at).split('T')[0] <= endDate);
              return (!query || inAction || inDetails) && afterStart && beforeEnd;
            });
            if (!filtered.length) return <div className="admin-user-card">No activity found</div>;
            const start = (page - 1) * pageSize;
            const pageItems = filtered.slice(start, start + pageSize);
            return pageItems.map((a) => (
              <div key={a.id} className="admin-user-card">
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{a.action}</div>
                    <div style={{ color: "#94a3b8", fontSize: 12 }}>{a.created_at ? String(a.created_at).split("T")[0] : ""}</div>
                  </div>
                  <div style={{ fontSize: 12, color: "#94a3b8" }}>{a.user_id || a.user}</div>
                </div>
                <div style={{ marginTop: 8 }}><pre style={{ whiteSpace: "pre-wrap" }}>{a.details ? JSON.stringify(a.details, null, 2) : ""}</pre></div>
              </div>
            ));
          })()}
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button className="text-button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
          <div style={{ alignSelf: 'center' }}>Page {page}</div>
          <button className="text-button" onClick={() => setPage((p) => p + 1)} disabled={activities.length === 0}>Next</button>
        </div>
      </div>
    </section>
  );
}

import { useEffect, useState } from "react";
import { fetchUserActivity, fetchActivity, getUsers } from "../api";

function formatDateTime(value) {
    if (!value) return "";
    return String(value).replace("T", " ").split(".")[0];
}

function getActivitySummary(activity) {
    const details = activity?.details && typeof activity.details === "object" ? activity.details : {};
    const stock = details.stock || activity.resource || "—";
    const mode = details.mode || null;
    const timeframe = details.timeframe || null;
    const startDate = details.start_date || "";
    const endDate = details.end_date || "";
    const features = Array.isArray(details.features) ? details.features.join(", ") : "";

    return {
        stock,
        mode,
        timeframe,
        period: startDate && endDate ? `${startDate} to ${endDate}` : startDate || endDate || "",
        features,
    };
}

function renderDetailValue(value) {
    if (Array.isArray(value)) {
        return value.join(", ");
    }
    if (value && typeof value === "object") {
        return JSON.stringify(value);
    }
    return String(value);
}

export default function ActivityPage({ token, initialUserId }) {
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
    const [expandedDetails, setExpandedDetails] = useState({});

    const toggleDetails = (activityId) => {
        setExpandedDetails((prev) => ({
            ...prev,
            [activityId]: !prev[activityId],
        }));
    };

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
        if (!token) return;
        let active = true;
        const load = async () => {
            setLoading(true);
            setError("");
            try {
                let payload;
                if (selectedUser) {
                    payload = await fetchUserActivity(token, selectedUser, { q: query, start: startDate, end: endDate, page, page_size: pageSize });
                } else {
                    payload = await fetchActivity(token, { q: query, start: startDate, end: endDate, page, page_size: pageSize });
                }
                // expect server to return an array or { items: [], total: N }
                const items = Array.isArray(payload) ? payload : (payload.items || payload.data || []);
                if (active) setActivities(items || []);
            } catch (err) {
                if (active) setError(err.message || "Failed to load activity");
            } finally {
                if (active) setLoading(false);
            }
        };
        load();
        return () => { active = false; };
    }, [token, selectedUser, query, startDate, endDate, page]);

    return (
        <section className="page-split single-column">
            <div className="page-panel">
                <div className="page-intro">
                    <p className="eyebrow">Activity</p>
                    <h2>Audit log</h2>
                    <p>Filter by user to inspect recent actions.</p>
                </div>

                <div className="activity-filter">
                    <select value={selectedUser} onChange={(e) => { setSelectedUser(e.target.value); setPage(1); }} className="admin-select">
                            <option value="">All users</option>
                        {users.map((u) => (
                            <option key={u.id} value={u.id}>{u.username}</option>
                        ))}
                    </select>
                    <input placeholder="Search actions/details" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} className="admin-input activity-query-input" />
                    <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }} className="admin-input" />
                    <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }} className="admin-input" />
                </div>
                <div className="filter-buttons">
                    <button className="primary-button" onClick={() => { setPage(1); }} type="button">Apply</button>
                    <button className="primary-button" onClick={() => {
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
                        a.download = `${selectedUser ? `user-${selectedUser}` : 'all-activity'}-export.json`;
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
                        const startIdx = (page - 1) * pageSize;
                        const pageItems = filtered.slice(startIdx, startIdx + pageSize);
                        return pageItems.map((a) => (
                            <div key={a.id} className="admin-user-card activity-card">
                                <div className="activity-card-body">
                                    <div className="activity-card-main">
                                        {(() => {
                                            const summary = getActivitySummary(a);
                                            return (
                                                <>
                                                    <div className="activity-card-title">{a.action} <span className="activity-card-resource">on {summary.stock}</span></div>
                                                    <div className="activity-card-tags">
                                                        {summary.timeframe && <span className="activity-tag activity-tag-timeframe">{summary.timeframe}</span>}
                                                        {summary.period && <span className="activity-tag activity-tag-period">{summary.period}</span>}
                                                    </div>
                                                </>
                                            );
                                        })()}
                                        <div className="activity-card-actions">
                                            {a.details && typeof a.details === 'object' ? (
                                                <button
                                                    type="button"
                                                    className="text-button activity-toggle-button"
                                                    onClick={() => toggleDetails(a.id)}
                                                >
                                                    {expandedDetails[a.id] ? 'Hide details' : 'Show details'}
                                                </button>
                                            ) : null}
                                        </div>
                                        {
                                            expandedDetails[a.id] && 
                                            <div className={`hidden-details ${expandedDetails[a.id] ? 'visible' : ''}`}>
                                            {expandedDetails[a.id] && a.details && typeof a.details === 'object' ? (
                                                <div className="activity-card-details">
                                                    <div className="activity-detail-row">
                                                        <div className="activity-detail-label">Time:</div>
                                                        <div className="activity-detail-value">{formatDateTime(a.created_at)}</div>
                                                    </div>
                                                    {Object.entries(a.details).map(([k, v]) => (
                                                        <div key={k} className="activity-detail-row">
                                                            <div className="activity-detail-label">{k.replace(/_/g, ' ')}:  </div>
                                                            <div className="activity-detail-value">{renderDetailValue(v)}</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : null}
                                        </div>
                                        }


                                    </div>
                                    <div className="activity-card-side">
                                        <div className="activity-card-user">{a.username || (a.user_id ? `User ${a.user_id}` : 'Unknown user')}</div>
                                    </div>
                                </div>
                            </div>
                        ));
                    })()}
                </div>

                <div className="activity-pagination">
                    <button className="text-button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
                    <div className="activity-pagination-label">Page {page}</div>
                    <button className="text-button" onClick={() => setPage((p) => p + 1)} disabled={activities.length === 0}>Next</button>
                </div>
            </div>
        </section>
    );
}

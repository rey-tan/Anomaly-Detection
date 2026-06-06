import React from 'react'

import { useEffect, useState } from "react";
import { fetchNotifications, markNotificationRead } from "../api";

export default function NotificationsPage({ token }) {

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let active = true;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await fetchNotifications(token);
        if (active) setNotifications(data || []);
      } catch (err) {
        if (active) setError(err.message || "Failed to load notifications");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [token]);

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(token, id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      // notify other components (header dropdown) to refresh their data
      try {
        window.dispatchEvent(new CustomEvent('notificationsUpdated', { detail: { id } }));
      } catch (e) {
        // ignore if dispatching fails in non-browser environments
      }
    } catch (err) {
      setError(err.message || "Failed to mark read");
    }
  };

  return (
    <section className="page-split">
        <div className="page-panel">
          <div className="page-intro">
            <p className="eyebrow">Notifications</p>
            <h2>Your recent alerts</h2>
            <p>System messages and progress updates appear here.</p>
          </div>

          {error ? <div className="form-error">{error}</div> : null}

          <div className="admin-list">
            {loading ? <div>Loading…</div> : null}
            {notifications.length === 0 && !loading ? <div className="empty-state-card"><h3>No notifications</h3></div> : null}
            {notifications.map((n) => (
              <div key={n.id} className={n.is_read ? "notification-card read" : "notification-card unread"}>
                <div className="notification-body">
                  <strong>{n.title}</strong>
                  <div className="notification-message">{n.message}</div>
                  <div className="notification-meta">{n.created_at ? String(n.created_at).split("T")[0] : ""} • {n.type}</div>
                </div>
                <div className="notification-actions">
                  {!n.is_read ? (
                    <button className="text-button" onClick={() => handleMarkRead(n.id)}>Mark read</button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>
    </section>
  );
}



import { useEffect, useMemo, useRef, useState } from "react";
import { fetchNotifications, markNotificationRead } from "../api";

function formatNotificationDate(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value).split("T")[0] : date.toLocaleDateString();
}

export default function NotificationsDropdown({ token, onOpenAll }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);
  // loadNotifications is called on mount and when an external update is signaled
  const loadNotifications = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const data = await fetchNotifications(token);
      setNotifications(data || []);
    } catch (err) {
      setError(err.message || "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
    // listen for external updates (e.g. another page marked a notification read)
    const handler = () => {
      loadNotifications();
    };
    window.addEventListener("notificationsUpdated", handler);
    return () => window.removeEventListener("notificationsUpdated", handler);
  }, [token]);

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.is_read).length,
    [notifications]
  );

  const previewNotifications = notifications.slice(0, 5);

  const handleMarkRead = async (notificationId) => {
    try {
      await markNotificationRead(token, notificationId);
      setNotifications((prev) =>
        prev.map((notification) =>
          notification.id === notificationId ? { ...notification, is_read: true } : notification
        )
      );
    } catch (err) {
      setError(err.message || "Failed to mark notification as read");
    }
  };

  const handleOpenAll = () => {
    setOpen(false);
    onOpenAll?.();
  };

  return (
    <div className="notification-dropdown" ref={containerRef}>
      <button
        className="notification-trigger"
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={unreadCount ? `Alerts, ${unreadCount} unread` : "Alerts"}
        onClick={() => setOpen((current) => !current)}
      >
        <span>Alerts</span>
        {unreadCount > 0 ? <strong>{unreadCount}</strong> : null}
      </button>

      {open ? (
        <div className="notification-popover" role="menu" aria-label="Notifications">
          <div className="notification-popover-head">
            <div>
              <p className="eyebrow">Notifications</p>
              <h3>Recent alerts</h3>
            </div>
          
          </div>

          {error ? <div className="notification-popover-error">{error}</div> : null}
          {loading ? <div className="notification-popover-empty">Loading…</div> : null}

          {!loading && previewNotifications.length === 0 ? (
            <div className="notification-popover-empty">
              <strong>No notifications yet</strong>
              <p>System updates and alerts will appear here.</p>
            </div>
          ) : null}

          {!loading && previewNotifications.length > 0 ? (
            <div className="notification-preview-list">
              {previewNotifications.map((notification) => (
                <article
                  key={notification.id}
                  className={notification.is_read ? "notification-preview read" : "notification-preview unread"}
                >
                  <div className="notification-preview-body">
                    <strong>{notification.title}</strong>
                    <p>{notification.message}</p>
                    <small>
                      {formatNotificationDate(notification.created_at)} {notification.type ? `• ${notification.type}` : ""}
                    </small>
                  </div>
                  {!notification.is_read ? (
                    <button
                      className="text-button"
                      type="button"
                      onClick={() => handleMarkRead(notification.id)}
                    >
                      Mark read
                    </button>
                  ) : null}
                </article>
              ))}
            </div>
          ) : null}

          <button className="notification-popover-footer" type="button" onClick={handleOpenAll}>
            View All Notifications
          </button>
        </div>
      ) : null}
    </div>
  );
}
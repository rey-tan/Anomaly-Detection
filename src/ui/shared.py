import streamlit as st
from datetime import datetime

from src.services.api_client import ApiError, get_notifications


def _format_notification_time(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)


def render_sidebar():
    st.sidebar.title("Controls")
    st.sidebar.markdown(f"**Logged in as:** {st.session_state['username']}")
    st.sidebar.markdown(f"**Role:** {st.session_state['role']}")

    if st.sidebar.button("Logout"):
        from src.ui.auth import logout

        logout()
        st.rerun()

    try:
        notifications = get_notifications(st.session_state["auth_token"])
    except ApiError:
        notifications = []
    except Exception:
        notifications = []

    if notifications:
        st.sidebar.markdown("### Notifications")
        for note in notifications[:5]:
            status = "✅" if note.get("is_read") else "🔔"
            title = note.get("title", "Notification")
            message = note.get("message", "")
            timestamp = _format_notification_time(note.get("created_at"))
            if timestamp:
                st.sidebar.write(f"{status} [{timestamp}] **{title}**: {message}")
            else:
                st.sidebar.write(f"{status} **{title}**: {message}")

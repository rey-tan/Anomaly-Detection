import streamlit as st
from datetime import datetime

from src.services.api_client import ApiError, get_user_profile, get_notifications


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


def profile_page():
    st.title("👤 Profile")

    try:
        profile = get_user_profile(st.session_state["auth_token"])
    except ApiError as exc:
        st.error(f"Unable to load profile: {exc}")
        return

    st.markdown(f"**Username:** {profile.get('username')}")
    st.markdown(f"**Role:** {profile.get('role')}")
    st.markdown(f"**Active:** {profile.get('is_active')}")
    st.markdown(f"**Created:** {profile.get('created_at')}")

    st.markdown("---")
    st.subheader("Notifications")

    try:
        notifications = get_notifications(st.session_state["auth_token"])
    except ApiError as exc:
        st.error(f"Unable to load notifications: {exc}")
        return

    if not notifications:
        st.info("No notifications available.")
        return

    for note in notifications:
        status = "✅" if note.get("is_read") else "🔔"
        timestamp = _format_notification_time(note.get("created_at"))
        header = f"{status} [{timestamp}] **{note.get('title')}**" if timestamp else f"{status} **{note.get('title')}**"
        st.write(header)
        st.write(note.get("message"))
        st.write("---")

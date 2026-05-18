import streamlit as st

from src.streamlit_components.admin import admin_page
from src.ui.auth import ensure_session_state, show_login_page
from src.ui.shared import render_sidebar

st.set_page_config(page_title="Admin", layout="wide")

ensure_session_state()

if not st.session_state["authenticated"]:
    show_login_page()
else:
    render_sidebar()
    admin_page()

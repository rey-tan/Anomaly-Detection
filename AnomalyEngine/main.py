import streamlit as st
from src.ui.auth import ensure_session_state, show_login_page
from src.ui.shared import render_sidebar


st.set_page_config(layout="centered", page_title="Anomaly Engine")

ensure_session_state()


if not st.session_state["authenticated"]:
    show_login_page()
else:
    render_sidebar()
    st.title("📊 Dashboard")

    st.markdown("Welcome to the Anomaly Engine dashboard. Use the side menu to navigate between analysis, realtime simulation, anomaly exploration, insights, and admin controls.")

    if st.session_state.get("results"):
        st.subheader("Most Recent Analysis")
        results = st.session_state["results"]
        st.write(results)
    else:
        st.info("Run an analysis from the Analysis page to see results here.")


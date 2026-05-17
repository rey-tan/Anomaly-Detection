import streamlit as st


def insights_page():
    st.title("💡 Insights")

    st.markdown(
        "Insights are generated from the latest analysis results and trend metrics. "
        "Use this page to explore anomaly counts, distribution, and performance signals."
    )

    results = st.session_state.get("results")
    if not results:
        st.info("Run an analysis to view insights.")
        return

    metrics = results.get("metrics", {})
    if metrics:
        st.subheader("Metrics")
        st.json(metrics)
    else:
        st.warning("No metrics available in the current result.")

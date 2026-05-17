import pandas as pd
import streamlit as st

from src.analysis.candlestick_visualizer import CandlestickAnomalyVisualizer
from src.components.visualization import plot_timeseries


def anomalies_page():
    st.title("🧩 Detected Anomalies")

    results = st.session_state.get("results")
    if not results:
        st.info("No analysis results available yet. Run an analysis or realtime simulation first.")
        return

    data = results.get("data", [])
    if not data:
        st.warning("Analysis returned no data.")
        return

    df = pd.DataFrame(data)
    if "transaction_time" in df.columns:
        df["transaction_time"] = pd.to_datetime(df["transaction_time"])
        df = df.set_index("transaction_time")

    if "cluster" in df.columns:
        anomalies = df[df["cluster"] == -1]
    else:
        anomalies = df

    st.subheader("Anomaly Table")
    st.dataframe(anomalies)

    if not anomalies.empty:
        st.subheader("Anomaly Statistics")
        st.write({
            "Total anomalies": len(anomalies),
            "Total rows": len(df),
        })

        tabs = st.tabs(["Anomaly Timeline", "Model Comparison", "DBSCAN Scatter"])

        with tabs[0]:
            if "close" in df.columns:
                fig = plot_timeseries("Anomaly Data", df, "1D")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Price timeline data is not available.")

        with tabs[1]:
            if all(c in df.columns for c in ["cluster_dbscan", "cluster_isolation_forest", "cluster_zscore", "open", "high", "low", "close"]):
                visualizer = CandlestickAnomalyVisualizer("Anomaly Comparison", df, timeframe="1D")
                comparison_fig = visualizer.plot_comparison()
                st.plotly_chart(comparison_fig, use_container_width=True)
            else:
                st.info("Comparison chart requires DBSCAN, Isolation Forest, and Z-score fields.")

        with tabs[2]:
            if "cluster" in df.columns and "volume" in df.columns:
                fig = plot_timeseries("DBSCAN Anomaly Data", df, "1D")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Scatter or DBSCAN visualization is not available.")

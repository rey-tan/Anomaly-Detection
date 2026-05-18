import pandas as pd
import streamlit as st
from datetime import date

from src.analysis.candlestick_visualizer import CandlestickAnomalyVisualizer
from src.components.visualization import plot_analysis, plot_scatter, plot_timeseries
from src.services.api_client import ApiError, analyze, save_cache
from src.utils.load import load_config, load_json
from src.utils.paths import ARTIFACTS, CONFIG
from src.utils.timeframes import VALID_TIMEFRAMES

app_config = load_config(CONFIG / "config.yaml")


def realtime_simulation_page():
    st.title("⏱️ Realtime Simulation")

    stock_options = sorted(load_json(ARTIFACTS / "allowed_symbols.json"))
    stock = st.selectbox("Symbol", stock_options)

    start_date = st.date_input(
        "Start Date",
        value=date(2026, 1, 1),
        min_value=date(2023, 1, 1),
        max_value=date.today(),
    )
    end_date = st.date_input(
        "End Date",
        value=date(2026, 1, 30),
        min_value=date(2023, 1, 1),
        max_value=date.today(),
    )

    timeframe = st.selectbox("Timeframe", VALID_TIMEFRAMES, index=1)

    if st.button("Run Realtime Simulation"):
        payload = {
            "stock": stock,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "timeframe": timeframe,
            "features": app_config["features"],
            "mode": "Realtime Simulation",
        }
        try:
            results = analyze(st.session_state["auth_token"], payload)
            st.session_state["results"] = results
            try:
                save_cache(st.session_state["auth_token"], payload, results)
            except ApiError as exc:
                st.warning(f"Result stored, but cache save failed: {exc}")
            st.success("Realtime simulation complete!")
        except ApiError as exc:
            st.error(f"Simulation failed: {exc}")
        except Exception as exc:
            st.error(f"Simulation failed: {exc}")

    if st.session_state["results"]:
        st.subheader("Latest Simulation Result")
        results = st.session_state["results"]
        data = results.get("data", [])
        if data:
            df = pd.DataFrame(data)
            if "transaction_time" in df.columns:
                df["transaction_time"] = pd.to_datetime(df["transaction_time"])
                df = df.set_index("transaction_time")

            st.markdown("### Charts")
            tabs = st.tabs(["Price Timeline", "Technical Indicators", "Method Comparison"])

            with tabs[0]:
                if "close" in df.columns:
                    fig = plot_timeseries(stock, df, timeframe)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No price data available for timeline chart.")

            with tabs[1]:
                if all(col in df.columns for col in ["SMA_10", "SMA_50", "Upper_BB", "Lower_BB"]):
                    fig = plot_analysis(stock, df, timeframe)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Technical indicators are not available for this dataset yet.")

            with tabs[2]:
                if all(c in df.columns for c in ["cluster_dbscan", "cluster_isolation_forest", "cluster_zscore", "open", "high", "low", "close"]):
                    visualizer = CandlestickAnomalyVisualizer(stock, df, timeframe=timeframe)
                    comparison_fig = visualizer.plot_comparison()
                    st.plotly_chart(comparison_fig, use_container_width=True)
                elif "cluster" in df.columns:
                    fig = plot_scatter(stock, df, timeframe)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No model comparison data is available yet.")

            with st.expander("Result metrics"):
                st.json(results.get("metrics", {}))

        st.write(results)

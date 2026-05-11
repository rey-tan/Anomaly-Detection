from src.pipelines import run_pipeline
from src.components.visualization import plot_scatter,plot_timeseries
from src.utils.load import load_config,load_json
from src.utils.paths import CONFIG,ARTIFACTS
import warnings
import streamlit as st
from datetime import date,datetime

warnings.filterwarnings("ignore")


config = load_config(CONFIG / "config.yaml")
best_params = load_json(ARTIFACTS / "best_params.json")


st.title(f"📊 Anomaly Detection Dashboard - {config['stock']}")

st.sidebar.title("⚙️ Controls")

stock = st.sidebar.text_input("Stock Symbol", value="NABIL")

start_date = st.sidebar.date_input(
    "Start Date",
    value=date(2026, 1, 1)
)

end_date = st.sidebar.date_input(
    "End Date",
    value=date(2026, 1, 30)
)
timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1min", "5min", "1D"],
    index=1
)



if st.sidebar.button("Run Analysis"):
    config = {
        "stock": stock,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "timeframe": timeframe,
        "features": config["features"]
    }
    results = run_pipeline(config, best_params)

    st.session_state["results"] = results



if "results" not in st.session_state:
    st.warning("Click 'Run Analysis' to generate results")
    st.stop()

results = st.session_state["results"]
df = results["data"]



st.subheader("📈 Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Rows", len(df))
col2.metric("Anomalies", (df["cluster"] == -1).sum())
col3.metric("Anomaly %", f"{(df['cluster'] == -1).mean()*100:.2f}%")


st.subheader("🔍 Anomalies")

st.dataframe(df[df["cluster"] == -1])



st.subheader("📉 Visualization")

fig1 = plot_scatter(config["stock"], df)
fig2 = plot_timeseries(config["stock"], df)

st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)


# Inspect and optionally save the top-N anomalies from the test period

# TopAnoms = df_test.sort_values(f"anomaly_score_{model}", ascending=False).head(top_n)
# print(str.upper(f"for {model} model"))
# print(f"The anomaly threshold is {threshold}")
# print(f"Top {top_n} most anomalous dates in test set:")
# print(TopAnoms[['close', 'quantity', 'return', f"anomaly_score_{model}", f"anomalous_{model}"]])
# print()



#MAJOR EVENTS
#2025-09-* is the GENZ Revolution

#20**-07-* is the Federal Budget Season

#2026-03-09 NEPSE Hits 6% circuit breaker after R.S.P Win
#The next day 2026-03-10 ppl boooked profits and it fell

#2026-03-29 After formation of new govt Oli and Lekhak were arrested leading to NEPSE falling
#2026-04-05 Jagadamba Group CEO was arrested leading to NEPSE freefall 
#2026-03-22 Official win of R.S.P
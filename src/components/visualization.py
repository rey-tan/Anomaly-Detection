import plotly.express as px
import plotly.graph_objects as go

def plot_scatter(symbol,df):
    df = df.copy().reset_index()

    df["color"] = df["cluster"].apply(
        lambda x: "Anomaly" if int(x) == -1 else "Normal"
    )

    fig = px.scatter(
        df,
        x="close",
        y="volume",
        color="color",
        color_discrete_map={
            "Anomaly": "red",
            "Normal": "blue"
        },
        title=f"DBSCAN Clustering Results on {symbol}",
        hover_data=["returns", "volatility","date"],
    )

    fig.update_layout(
        width=1200,
        height=600,
        legend_title="Legend",
    )

    return fig

def plot_timeseries(symbol,df):

    df = df.copy()
    fig = go.Figure()

    # price line
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["close"],
            mode="lines",
            name="Close",
            line=dict(width=2),
        )
    )

    # anomalies
    anomalies = df[df["cluster"] == -1]

    fig.add_trace(
        go.Scatter(
            x=anomalies.index,
            y=anomalies["close"],
            mode="markers",
            name="Anomalies",
            marker=dict(color="red", size=8),
        )
    )

    fig.update_layout(
        title=f"{symbol} Price with DBSCAN Anomalies",
        width=1200,
        height=600,
    )

    return fig
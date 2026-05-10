import plotly.express as px
import plotly.graph_objects as go

def plot_scatter(symbol,df):
    df = df.copy()

    df["color"] = df["cluster"].apply(lambda x: "red" if x == -1 else "blue")

    fig = px.scatter(
        df,
        x="close",
        y="volume",
        color="color",
        title=f"DBSCAN Clustering Results on {symbol}",
        hover_data=["returns", "volatility"],
    )

    fig.update_layout(
        width=1200,
        height=600,
        legend_title="Legend",
    )
    # fig.show

    return fig

def plot_timeseries(symbol,df):

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
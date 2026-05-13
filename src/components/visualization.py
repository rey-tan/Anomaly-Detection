import plotly.express as px
import plotly.graph_objects as go

def plot_analysis(symbol,df):
    df_filtered = df.copy()
    
    # df_filtered = df_filtered.between_time("11:00", "15:00")

    #create a sequence of numbers from 1 to len(df)
    df_filtered['candle_idx'] = range(len(df))
    # Create the figure
    fig = go.Figure()

    # Add 'Close' close line
    fig.add_trace(
        go.Scatter(
            # x=df_filtered.index,
            x=df_filtered['candle_idx'],
            y=df_filtered["close"],
            mode="lines",
            name="Close",
            line=dict(color="blue", width=2),
        )
    )

    # Add 'SMA 10' line
    fig.add_trace(
        go.Scatter(
           # x=df_filtered.index,
            x=df_filtered['candle_idx'],
            y=df_filtered["SMA_10"],
            mode="lines",
            name="SMA 10",
            line=dict(color="green", width=2, dash="dot"),
        )
    )

    # Add 'SMA 50' line
    fig.add_trace(
        go.Scatter(
            # x=df_filtered.index,
            x=df_filtered['candle_idx'],
            y=df_filtered["SMA_50"],
            mode="lines",
            name="SMA 50",
            line=dict(color="orange", width=2, dash="dash"),
        )
    )

    # Add 'Upper BB' line
    fig.add_trace(
        go.Scatter(
            # x=df_filtered.index,
            x=df_filtered['candle_idx'],
            y=df_filtered["Upper_BB"],
            mode="lines",
            name="Upper BB",
            line=dict(color="red", width=1, dash="dot"),
        )
    )

    # Add 'Lower BB' line
    fig.add_trace(
        go.Scatter(
            # x=df_filtered.index,
            x=df_filtered['candle_idx'],
            y=df_filtered["Lower_BB"],
            mode="lines",
            name="Lower BB",
            line=dict(color="purple", width=1, dash="dot"),
        )
    )

    # Update layout for a larger figure size and title
    fig.update_layout(
        title=f"{symbol} Stock close with Technical Indicators",
        xaxis_title="Date",
        yaxis_title="Stock close",
        legend=dict(
            x=0, y=1, bgcolor="rgba(255,255,255,0)", bordercolor="rgba(255,255,255,0)"
        ),
        autosize=False,
        width=1200,
        height=600,
    )

    fig.update_xaxes(showticklabels=False)  

    # fig.update_xaxes(
    #     rangebreaks=[
    #         dict(bounds=["sat", "sat"]),  # remove weekends
    #         dict(bounds=[15, 11], pattern="hour"),  # keep only 11–15
    #     ]
    # )

    return fig;

    

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
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_analysis(symbol, df, timeframe):
    df_filtered = df.copy()
    
    if timeframe != '1D':
        if not isinstance(df_filtered.index, pd.DatetimeIndex):
            if 'transaction_time' in df_filtered.columns:
                df_filtered['transaction_time'] = pd.to_datetime(df_filtered['transaction_time'])
                df_filtered = df_filtered.set_index('transaction_time')
            elif 'date' in df_filtered.columns:
                df_filtered['date'] = pd.to_datetime(df_filtered['date'])
                df_filtered = df_filtered.set_index('date')

        if isinstance(df_filtered.index, pd.DatetimeIndex):
            df_filtered = df_filtered.between_time("11:00", "15:00")


    fig = go.Figure()

    # Close price (primary y-axis)
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["close"],
        mode="lines",
        name="Close",
        line=dict(color="blue", width=2),
        yaxis="y1"
    ))

    # SMA 10 (primary y-axis)
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["SMA_10"],
        mode="lines",
        name="SMA 10",
        line=dict(color="green", width=1.5, dash="dot"),
        yaxis="y1"
    ))

    # SMA 50 (primary y-axis)
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["SMA_50"],
        mode="lines",
        name="SMA 50",
        line=dict(color="orange", width=1.5, dash="dash"),
        yaxis="y1"
    ))

    # Bollinger Bands (secondary y-axis)
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["Upper_BB"],
        mode="lines",
        name="Upper BB",
        line=dict(color="red", width=1),
        yaxis="y2"
    ))

    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["Lower_BB"],
        mode="lines",
        name="Lower BB",
        line=dict(color="red", width=1),
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.1)',
        yaxis="y2"
    ))

    fig.update_layout(
        title=f"{symbol} Stock Price with Technical Indicators",
        xaxis_title="Date",
        yaxis=dict(title="Price", side='left'),
        yaxis2=dict(title="Bollinger Bands", overlaying='y', side='right'),
        legend=dict(x=0, y=1),
        width=1200,
        height=600,
        hovermode='x unified'
    )

    rangebreaks = [dict()]
    if timeframe != '1D':
        rangebreaks.append(dict(bounds=[15, 11], pattern="hour"))

    fig.update_xaxes(
        type='date',
        tickformat='%Y-%m-%d %H:%M',
        rangebreaks=rangebreaks
    )

    return fig

def plot_scatter(symbol, df, timeframe):
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
        hover_data=["returns", "volatility"],
    )

    fig.update_layout(
        width=1200,
        height=600,
        legend_title="Legend",
    )

    return fig



def plot_timeseries(symbol, df, timeframe):

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
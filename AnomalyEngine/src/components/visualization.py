import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
    
    df["ensemble_label"] = df.apply(classify_ensemble, axis=1)
    df["z_label"] = df["Anomaly_Z_Score"].apply(z_label)

    critical = df[df["ensemble_label"] == "Critical Anomaly"]
    density = df[df["ensemble_label"] == "Density Based Anomaly"]
    structure = df[df["ensemble_label"] == "Structure Based Anomaly"]

    fig = go.Figure()

    # Add the line for the closing close
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["close"],
            mode="lines",
            name="Close prices",
            line=dict(color="blue"),
        )
    )

    # Critical anomalies
    fig.add_trace(
        go.Scatter(
            x=critical.index,
            y=critical["close"],
            mode="markers",
            name="Critical",
            hovertemplate=
            "Time: %{x}<br>" +
            "Price: %{y}<br>" +
            "Deviation: %{customdata[0]:.2f}σ<br>" +
            "<extra></extra>",
            customdata=np.stack([
                critical["Anomaly_Z_Score"]
            ], axis=-1),
            marker=dict(color="red", size=10)
        )
    )

    # Density anomalies
    fig.add_trace(
        go.Scatter(
            x=density.index,
            y=density["close"],
            mode="markers",
            name="Density",
            hovertemplate=
            "Time: %{x}<br>" +
            "Price: %{y}<br>" +
            "Deviation: %{customdata[0]:.2f}σ<br>" +
            "<extra></extra>",
            customdata=np.stack([
                density["Anomaly_Z_Score"]
            ], axis=-1),
            marker=dict(color="orange", size=8)
        )
    )

    # Structure anomalies
    fig.add_trace(
        go.Scatter(
            x=structure.index,
            y=structure["close"],
            mode="markers",
            name="Structure",
            hovertemplate=
            "Time: %{x}<br>" +
            "Price: %{y}<br>" +
            "Deviation: %{customdata[0]:.2f}σ<br>" +
            "<extra></extra>",
            customdata=np.stack([
                structure["Anomaly_Z_Score"]
            ], axis=-1),
            marker=dict(color="green", size=8)
        )
    )

    # Update layout
    fig.update_layout(
        title=f"{symbol} Stock close with Detected Anomalies",
        xaxis_title="Date",
        yaxis_title="Close prices",
        legend_title="Legend",
        width=1200,
        height=600,
    )

    return fig



def classify_ensemble(row):

    if row["Anomaly_Isolation_Forest"] == -1 and row["Anomaly_DBSCAN"] == -1:
        return "Critical Anomaly"

    elif row["Anomaly_DBSCAN"] == -1:
        return "Density Based Anomaly"

    elif row["Anomaly_Isolation_Forest"] == -1:
        return "Structure Based Anomaly"

    return "Normal"

def z_label(z):
    if abs(z) < 1:
        return "Normal (within 1σ)"
    elif abs(z) < 2:
        return "Mild deviation (1–2σ)"
    elif abs(z) < 3:
        return "Strong deviation (2–3σ)"
    else:
        return "Extreme deviation (>3σ)"
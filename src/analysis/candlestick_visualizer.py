"""
OHLC Candlestick Visualization with Anomaly Detection
Handles multiple timeframes and shows anomalies clearly on candlesticks
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class CandlestickAnomalyVisualizer:
    """
    Advanced visualizer for candlestick charts with anomaly highlighting.
    """
    
    def __init__(self, symbol: str, df: pd.DataFrame, timeframe: str = '1D'):
        """
        Initialize visualizer.
        
        Parameters:
        -----------
        symbol : str
            Stock symbol (e.g., 'CHCL')
        df : pd.DataFrame
            DataFrame with OHLC data and cluster/anomaly column
            Required columns: open, high, low, close, volume, cluster (or similar)
        timeframe : str
            Timeframe for display purposes ('1min', '5min', '1D', etc.)
        """
        self.symbol = symbol
        self.df = df.copy()
        self.timeframe = timeframe
        self._validate_data()
    
    def _validate_data(self):
        """Check that required columns exist."""
        required = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required if col not in self.df.columns]
        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Check for cluster/anomaly column
        if 'cluster' not in self.df.columns:
            if 'anomaly' in self.df.columns:
                self.df['cluster'] = self.df['anomaly'].apply(lambda x: -1 if x else 1)
            else:
                raise ValueError("Need 'cluster' or 'anomaly' column")
    
    def _add_candlesticks(self, fig: go.Figure, show_volume: bool = True):
        """
        Add candlestick trace to figure.
        
        Parameters:
        -----------
        fig : go.Figure
            Plotly figure to add to
        show_volume : bool
            Whether to include volume information
        """
        # Separate bullish and bearish candles
        bullish = self.df[self.df['close'] >= self.df['open']]
        bearish = self.df[self.df['close'] < self.df['open']]
        
        # Add bullish candles (green)
        fig.add_trace(
            go.Candlestick(
                x=bullish.index,
                open=bullish['open'],
                high=bullish['high'],
                low=bullish['low'],
                close=bullish['close'],
                name='Bullish',
                increasing_line_color='green',
                increasing_fillcolor='rgba(0, 255, 0, 0.7)',
                decreasing_line_color='green',
                decreasing_fillcolor='rgba(0, 255, 0, 0.1)',
            )
        )
        
        # Add bearish candles (red)
        fig.add_trace(
            go.Candlestick(
                x=bearish.index,
                open=bearish['open'],
                high=bearish['high'],
                low=bearish['low'],
                close=bearish['close'],
                name='Bearish',
                increasing_line_color='red',
                increasing_fillcolor='rgba(255, 0, 0, 0.1)',
                decreasing_line_color='red',
                decreasing_fillcolor='rgba(255, 0, 0, 0.7)',
            )
        )
    
    def _add_anomaly_highlights(self, fig: go.Figure, 
                                anomaly_color: str = 'orange',
                                anomaly_width: int = 3):
        """
        Add anomaly highlighting as shapes around candlesticks.
        
        Parameters:
        -----------
        fig : go.Figure
            Plotly figure to add to
        anomaly_color : str
            Color for anomaly highlights
        anomaly_width : int
            Width of highlight border
        """
        anomalies = self.df[self.df['cluster'] == -1]
        
        if len(anomalies) == 0:
            return
        
        # Add rectangles around anomaly candles
        for idx, (date, row) in enumerate(anomalies.iterrows()):
            # Create small offset for rectangle visibility
            if isinstance(date, pd.Timestamp):
                x_center = date
            else:
                x_center = idx
            
            # Rectangle around the high-low range
            fig.add_shape(
                type="rect",
                x0=x_center,
                x1=x_center,
                y0=row['low'] * 0.99,  # Slightly below the low
                y1=row['high'] * 1.01,  # Slightly above the high
                line=dict(color=anomaly_color, width=anomaly_width),
                fillcolor=f"rgba({self._color_to_rgb(anomaly_color)}, 0.1)",
            )
    
    def _add_anomaly_markers(self, fig: go.Figure, 
                            marker_position: str = 'high',
                            marker_size: int = 10):
        """
        Add marker points at anomaly locations.
        
        Parameters:
        -----------
        fig : go.Figure
            Plotly figure to add to
        marker_position : str
            'high', 'low', or 'close' - where to place marker
        marker_size : int
            Size of marker
        """
        anomalies = self.df[self.df['cluster'] == -1]
        
        if len(anomalies) == 0:
            return
        
        # Choose y position for marker
        if marker_position == 'high':
            y_vals = anomalies['high']
            marker_name = "Anomalies (High)"
        elif marker_position == 'low':
            y_vals = anomalies['low']
            marker_name = "Anomalies (Low)"
        else:  # close
            y_vals = anomalies['close']
            marker_name = "Anomalies (Close)"
        
        fig.add_trace(
            go.Scatter(
                x=anomalies.index,
                y=y_vals,
                mode='markers',
                name=marker_name,
                marker=dict(
                    color='red',
                    size=marker_size,
                    symbol='diamond',
                    line=dict(color='darkred', width=2)
                ),
                hovertemplate='<b>Anomaly</b><br>Date: %{x}<br>Price: %{y}<extra></extra>'
            )
        )
    
    def _add_volume_subplot(self, fig: go.Figure):
        """
        Add volume bars as secondary subplot.
        
        Parameters:
        -----------
        fig : go.Figure
            Plotly figure to add to
        """
        # Separate bullish and bearish volumes
        bullish = self.df[self.df['close'] >= self.df['open']]
        bearish = self.df[self.df['close'] < self.df['open']]
        
        # Add bullish volume (green)
        fig.add_trace(
            go.Bar(
                x=bullish.index,
                y=bullish['volume'],
                name='Volume (Bullish)',
                marker_color='rgba(0, 255, 0, 0.5)',
                yaxis='y2',
            )
        )
        
        # Add bearish volume (red)
        fig.add_trace(
            go.Bar(
                x=bearish.index,
                y=bearish['volume'],
                name='Volume (Bearish)',
                marker_color='rgba(255, 0, 0, 0.5)',
                yaxis='y2',
            )
        )
    
    def _add_sma(self, fig: go.Figure, window: int = 20):
        """
        Add Simple Moving Average line.
        
        Parameters:
        -----------
        fig : go.Figure
            Plotly figure to add to
        window : int
            Window size for SMA
        """
        if len(self.df) < window:
            return
        
        sma = self.df['close'].rolling(window=window).mean()
        
        fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=sma,
                name=f'SMA {window}',
                line=dict(color='blue', width=2, dash='dash'),
                hovertemplate='SMA %{y:.2f}<extra></extra>'
            )
        )
    
    def _color_to_rgb(self, color_name: str) -> str:
        """Convert color name to RGB values."""
        colors = {
            'red': '255, 0, 0',
            'green': '0, 255, 0',
            'blue': '0, 0, 255',
            'orange': '255, 165, 0',
            'yellow': '255, 255, 0',
        }
        return colors.get(color_name.lower(), '0, 0, 0')
    
    def plot_candlestick_with_anomalies(self, 
                                       show_volume: bool = True,
                                       show_sma: bool = True,
                                       sma_window: int = 20,
                                       anomaly_marker: str = 'highlight',
                                       width: int = 1400,
                                       height: int = 700) -> go.Figure:
        """
        Create comprehensive candlestick chart with anomaly highlighting.
        
        Parameters:
        -----------
        show_volume : bool
            Show volume bars
        show_sma : bool
            Show Simple Moving Average
        sma_window : int
            Window for SMA calculation
        anomaly_marker : str
            'highlight' (boxes), 'marker' (diamonds), or 'both'
        width : int
            Chart width
        height : int
            Chart height
        
        Returns:
        --------
        go.Figure : Plotly figure
        """
        
        # Create figure with secondary y-axis if showing volume
        if show_volume:
            fig = go.Figure()
            
            # Add candlesticks
            self._add_candlesticks(fig, show_volume=False)
            
            # Add anomaly highlighting
            if anomaly_marker in ['highlight', 'both']:
                self._add_anomaly_highlights(fig)
            
            if anomaly_marker in ['marker', 'both']:
                self._add_anomaly_markers(fig)
            
            # Add SMA
            if show_sma:
                self._add_sma(fig, sma_window)
            
            # Add volume
            self._add_volume_subplot(fig)
            
            # Update layout with dual y-axes
            fig.update_layout(
                title=f"{self.symbol} ({self.timeframe}) - Candlestick with Anomalies",
                yaxis_title="Price",
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right"
                ),
                xaxis_title="Date",
                template="plotly_white",
                height=height,
                width=width,
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
            )
        else:
            fig = go.Figure()
            
            # Add candlesticks
            self._add_candlesticks(fig, show_volume=False)
            
            # Add anomaly highlighting
            if anomaly_marker in ['highlight', 'both']:
                self._add_anomaly_highlights(fig)
            
            if anomaly_marker in ['marker', 'both']:
                self._add_anomaly_markers(fig)
            
            # Add SMA
            if show_sma:
                self._add_sma(fig, sma_window)
            
            fig.update_layout(
                title=f"{self.symbol} ({self.timeframe}) - Candlestick with Anomalies",
                yaxis_title="Price",
                xaxis_title="Date",
                template="plotly_white",
                height=height,
                width=width,
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
            )
        
        # X-axis configuration for different timeframes
        self._configure_xaxis(fig)
        
        return fig
    
    def _configure_xaxis(self, fig: go.Figure):
        """Configure x-axis based on timeframe."""
        timeframe_config = {
            '1min': dict(
                rangebreaks=[
                    dict(bounds=["sat", "sun"]),  # Hide weekends
                    dict(bounds=[16, 9], pattern="hour"),  # Hide after-hours
                ],
                rangeslider=dict(visible=False),
            ),
            '5min': dict(
                rangebreaks=[
                    dict(bounds=["sat", "sun"]),
                    dict(bounds=[16, 9], pattern="hour"),
                ],
                rangeslider=dict(visible=False),
            ),
            '1D': dict(
                rangeslider=dict(visible=False),
                rangebreaks=[
                    dict(bounds=["sat", "sun"]),
                ]
            ),
        }
        
        config = timeframe_config.get(self.timeframe, dict(rangeslider=dict(visible=False)))
        fig.update_xaxes(config)
    
    def plot_comparison(self, methods: list = ['dbscan', 'isolation_forest', 'zscore']) -> go.Figure:
        """
        Create side-by-side comparison of different anomaly detection methods.
        
        Parameters:
        -----------
        methods : list
            List of anomaly detection methods to compare
        
        Returns:
        --------
        go.Figure : Subplot figure with comparison
        """
        n_methods = len(methods)
        
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=n_methods,
            cols=1,
            subplot_titles=[f"Method: {m.upper()}" for m in methods],
            shared_xaxes=True,
            specs=[[{"secondary_y": False}] for _ in range(n_methods)]
        )
        
        for idx, method in enumerate(methods, 1):
            # Check if method column exists
            if f'cluster_{method}' not in self.df.columns:
                continue
            
            # Filter data for this method
            df_method = self.df.copy()
            df_method['cluster'] = df_method[f'cluster_{method}']
            
            # Separate bullish and bearish
            bullish = df_method[df_method['close'] >= df_method['open']]
            bearish = df_method[df_method['close'] < df_method['open']]
            
            # Add candlesticks
            fig.add_trace(
                go.Candlestick(
                    x=bullish.index,
                    open=bullish['open'],
                    high=bullish['high'],
                    low=bullish['low'],
                    close=bullish['close'],
                    name=f'{method} (Bull)',
                    increasing_line_color='green',
                    increasing_fillcolor='rgba(0, 255, 0, 0.7)',
                ),
                row=idx,
                col=1
            )
            
            fig.add_trace(
                go.Candlestick(
                    x=bearish.index,
                    open=bearish['open'],
                    high=bearish['high'],
                    low=bearish['low'],
                    close=bearish['close'],
                    name=f'{method} (Bear)',
                    increasing_line_color='red',
                    increasing_fillcolor='rgba(255, 0, 0, 0.1)',
                ),
                row=idx,
                col=1
            )
            
            # Add anomalies
            anomalies = df_method[df_method['cluster'] == -1]
            if len(anomalies) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=anomalies.index,
                        y=anomalies['high'],
                        mode='markers',
                        name=f'{method} Anomalies',
                        marker=dict(color='red', size=8, symbol='diamond'),
                    ),
                    row=idx,
                    col=1
                )
        
        fig.update_layout(
            title=f"{self.symbol} - Anomaly Detection Methods Comparison",
            height=300 * n_methods,
            width=1400,
            hovermode='x unified',
        )
        
        return fig


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Simple candlestick with anomaly markers
───────────────────────────────────────────────────

import pandas as pd

df = pd.read_csv('CHCL_1min.csv', index_col='date', parse_dates=True)

visualizer = CandlestickAnomalyVisualizer('CHCL', df, timeframe='1min')
fig = visualizer.plot_candlestick_with_anomalies(
    show_volume=True,
    show_sma=True,
    anomaly_marker='both'  # Show both highlights and markers
)
fig.show()

#   visualizer = CandlestickAnomalyVisualizer(stock, df, timeframe)
#     fig = visualizer.plot_candlestick_with_anomalies(
#         show_volume=True,
#         show_sma=True,
#         anomaly_marker='both'  # Show both highlights and markers
#     )

#     st.plotly_chart(fig)


Example 2: Comparison of multiple methods
──────────────────────────────────────────

# Add cluster columns for different methods
df['cluster_dbscan'] = dbscan_predictions
df['cluster_isolation_forest'] = if_predictions
df['cluster_zscore'] = zscore_predictions

visualizer = CandlestickAnomalyVisualizer('CHCL', df, timeframe='1min')
fig = visualizer.plot_comparison(
    methods=['dbscan', 'isolation_forest', 'zscore']
)
fig.show()


Example 3: Different timeframes
──────────────────────────────

for timeframe in ['1min', '5min', '1D']:
    df = load_data('CHCL', timeframe)
    
    visualizer = CandlestickAnomalyVisualizer('CHCL', df, timeframe=timeframe)
    fig = visualizer.plot_candlestick_with_anomalies()
    fig.show()
"""


def plot_candlestick(symbol: str, df: pd.DataFrame, timeframe: str = '1D',
                    show_volume: bool = True, show_sma: bool = True) -> go.Figure:
    """
    Quick function to plot candlestick chart.
    
    Parameters:
    -----------
    symbol : str
        Stock symbol
    df : pd.DataFrame
        OHLC data with 'cluster' column
    timeframe : str
        Timeframe for display
    show_volume : bool
        Show volume
    show_sma : bool
        Show SMA
    
    Returns:
    --------
    go.Figure : Plotly figure
    """
    visualizer = CandlestickAnomalyVisualizer(symbol, df, timeframe)
    return visualizer.plot_candlestick_with_anomalies(
        show_volume=show_volume,
        show_sma=show_sma,
        anomaly_marker='both'
    )


if __name__ == "__main__":
    print("CandlestickAnomalyVisualizer loaded successfully")
    print("\nUsage:")
    print("  visualizer = CandlestickAnomalyVisualizer('CHCL', df, timeframe='1min')")
    print("  fig = visualizer.plot_candlestick_with_anomalies()")
    print("  fig.show()")
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64


# matplotlib.use("TkAgg")

def plot_results(mode, stock_name, threshold, df, period,model):
    """
    Plot financial data with different handling for Train vs Test periods.
    """

    
    plt.figure(figsize=(20, 10))
    
    df_plot = df.copy()
    days_count = len(np.unique(df_plot.index.date))
    
    # Filter to trading hours if intraday
    if mode == "Intraday":  
        df_plot = df_plot[
            (df_plot.index.hour >= 11) & (df_plot.index.hour < 15)
        ]
    
    # Create sequential x-axis for clean plotting
    x_values = np.arange(len(df_plot))
    
    # Plot lines
    plt.plot(x_values, df_plot['close'], label=f"{stock_name} close ({period} Period)")
    if 'SMA_5' in df_plot.columns:
        plt.plot(x_values, df_plot['SMA_5'], label='SMA 5', linestyle='--', zorder=3)
    
    if 'SMA_20' in df_plot.columns:
        plt.plot(x_values, df_plot['SMA_20'], label='SMA 20', linestyle='--', zorder=3)

    if 'EMA_10' in df_plot.columns:
        plt.plot(x_values, df_plot['EMA_10'], label='EMA 10', linestyle='-.', zorder=3)
    
    # Plot anomalies
    anomaly_mask = df_plot[f"anomalous_{model}"].values
    plt.scatter(
        x_values[anomaly_mask],
        df_plot.loc[anomaly_mask, 'close'].values,
        color='red',
        label=f"Detected anomalies ({period})",
        zorder=5,
    )
    
    # Set x-axis labels based on period
    if mode == "Intraday" and period == "Test":
        # Test: Show ~6 labels per day (times only)
        step = max(1, len(x_values) // (6 * days_count))
        plt.xticks(
            x_values[::step],
            [t.strftime('%H:%M') for t in df_plot.index[::step]],
            rotation=45
        )
    elif mode == "Intraday" and period == "Train":
        # Train: Show dates only (one per day)
        step = max(1, len(x_values) // days_count)
        plt.xticks(
            x_values[::step],
            [t.strftime('%m-%d') for t in df_plot.index[::step]],
            rotation=45
        )
    else:
        # Daily data: Show date labels
        step = max(1, len(x_values) // 10)
        plt.xticks(
            x_values[::step],
            [t.strftime('%Y-%m-%d') for t in df_plot.index[::step]],
            rotation=45
        )
    


    title = f"{stock_name} close prices with {model} anomalies & Moving Averages in ({period} data)"
    plt.title(title)
    plt.xlabel('Transaction Time')
    plt.ylabel('Close Price')
    plt.legend()
    plt.tight_layout()
    # plt.show()
    img1 = fig_to_base64()
    plt.close()
    
    # Diagnostics
    title = f"Distribution of {model} anomaly scores ({period} set)"
    plt.figure(figsize=(12, 5))
    plt.hist(df_plot[f"anomaly_score_{model}"], bins=50, color='steelblue', edgecolor='black')
    plt.axvline(threshold, color='red', linestyle='--', label='Anomaly threshold')
    plt.title(title)
    plt.xlabel('Anomaly score (higher score = more anomalous)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    # plt.show()
    img2 = fig_to_base64()
    plt.close()

    
    # print(f'Anomaly counts in {period} set:')
    # print(df_plot[f"anomalous_{model}"].value_counts())

    return {
        "price_plot":img1,
        "histogram_plot":img2
    }




def fig_to_base64():
    buffer = BytesIO(); #create an in memory file
    plt.savefig(buffer,format="png",bbox_inches="tight") #write the image to a buffer
    buffer.seek(0) #when u save to a buffer the cursor is at the end so reset to 0 to read it

    img_base64 = base64.b64encode(buffer.read()).decode("utf-8") #read the raw png bytes -> then convert it into text safe base64 format -> now convert these bytes into UTF-8 
    buffer.close() # free the memory


    return img_base64
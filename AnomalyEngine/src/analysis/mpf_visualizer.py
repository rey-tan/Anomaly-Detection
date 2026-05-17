import mplfinance as mpf
from io import BytesIO
import base64
import matplotlib.pyplot as plt

def plot_ohlcv(stock_name,df,period):
    df_ohlcv = df[['open', 'high', 'low', 'close','quantity']].copy()
    df_ohlcv = df_ohlcv.rename(columns={'quantity':'volume'})
    
    fig, axlist = mpf.plot(
        df_ohlcv,
        type='candle',
        volume=True,
        style="yahoo",
        figsize=(50, 20),
        title=f"{stock_name} OHLCV {period} data chart",
        volume_panel=1,
        returnfig=True   
    )

    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    buffer.close()

    plt.close(fig)

    return img_base64



VALID_TIMEFRAMES = ["1min", "5min", "15min", "1H", "1D"]

#days
WINDOW_MAP = {
    "1D": 24 * 30,
    "1H": 6 * 30,
    "15min": 3 * 30,
    "5min": 2 * 30,
    "1min": 30
}
#1min is more noisier so requires more data points for smoothing it out
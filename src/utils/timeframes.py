VALID_TIMEFRAMES = ["1min", "5min", "15min", "1H", "1D", "2D"]

#days
WINDOW_MAP = {
    "2D": 24 * 30,
    "1D": 12 * 30,
    "1H": 3 * 30,
    "15min": 1 * 30,
    "5min": 7,
    "1min": 15
}
#1min is more noisier so requires more data points for smoothing it out
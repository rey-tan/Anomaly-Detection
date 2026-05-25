from datetime import date, timedelta

VALID_TIMEFRAMES = ["1min", "5min", "15min", "1H", "1D"]

#days
WINDOW_MAP = {
    "2D": 72 * 30,
    "1D": 36 * 30,
    # "1H": 6 * 30,
    # "15min": 3 * 30,
    # "5min": 2 * 30,
    # "1min": 30
}



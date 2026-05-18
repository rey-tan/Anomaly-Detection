from datetime import date, timedelta

VALID_TIMEFRAMES = ["1min", "5min", "15min", "1H", "1D"]

#days
WINDOW_MAP = {
    "1D": 36 * 30,
    "1H": 6 * 30,
    "15min": 3 * 30,
    "5min": 2 * 30,
    "1min": 30
}




def generate_market_holidays(start_date, end_date):
    current = start_date
    holidays = []

    switch_date = date(2026, 4, 6)

    while current <= end_date:
        # BEFORE April 6 2026
        if current < switch_date:
            if current.weekday() in [4, 5]:  # Fri=4 Sat=5
                holidays.append(current)  

        # AFTER April 6 2026
        else:
            if current.weekday() in [5, 6]:  # Sat=5 Sun=6
                holidays.append(current)  

        current += timedelta(days=1)

    return holidays
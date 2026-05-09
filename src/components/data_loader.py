import pandas as pd
from utils.paths import PROCESSED_DATA
from datetime import datetime

def load_data(stock_name,start_date,end_date):
    all_days = []
   
    for date_folder in sorted(PROCESSED_DATA.iterdir()):
        if not date_folder.is_dir():
            continue

        date = datetime.strptime(date_folder.name, "%Y-%m-%d")
        if start_date <= date <= end_date:
            file_path = date_folder / f"{stock_name}.csv"

            if file_path.exists():
                df = pd.read_csv(file_path)
                df["transaction_time"] = pd.to_datetime(df["transaction_time"])
                df = df.set_index("transaction_time")
                df = df.sort_index()

                all_days.append(df)

    if not all_days:
        # if no data found returns an empty dataframe
        df = pd.DataFrame()
    else:
        # else a concatenated dataframe and ignore the index of the dataframe and generate a brand new set of indices
        df = pd.concat(all_days).sort_index()
        df = df.reset_index()
    
    return df

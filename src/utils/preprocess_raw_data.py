from locale import normalize
from pathlib import Path
import pandas as pd
from datetime import date
import re
import paths
import json


with open(paths.CONFIG / "allowed_symbols.json","r") as f:
    allowed_symbols = set(json.load(f));

    
def preprocess_raw_data(date = "2025-01-01"):

    input = paths.RAW_DATA / f"floor-{date}.csv"
    output_dir = paths.PROCESSED_DATA / date
    

    df = pd.read_csv(Path(input), engine="python")

    output_dir.mkdir(parents=True, exist_ok=True)

    df["transaction_time"] = df["transaction_time"].astype(str)

    # 1. remove commas
    df["transaction_time"] = df["transaction_time"].str.replace(",", "", regex=False)

    # 2. fix ms safely using function
    def fix_ms(ts):
        match = re.match(r"(.*:\d{2}:\d{2}):(\d{1,3}) (AM|PM)", ts)
        if match:
            base = match.group(1)
            ms = match.group(2)

            # normalize to 3 digits safely
            ms = ms.zfill(3)

            return f"{base}.{ms} {match.group(3)}"

        return ts

    df["transaction_time"] = df["transaction_time"].apply(fix_ms)

    # 3. parse datetime
    df["transaction_time"] = pd.to_datetime(df["transaction_time"], errors="coerce")

    # bad_rows = df[df["transaction_time"].isna()]
    # print(bad_rows.head(20))
    
   
    df = df.drop(columns = [
        "contract_id",
        "buyer_member_id",
        "seller_member_id",
        "amount"
    ])

    

    tickers = df["symbol"].unique()

    for ticker in tickers:

        if ticker not in allowed_symbols:
            continue;

        ticker_df = df[df["symbol"] == ticker]

        # Replace any character that is not a letter, number, underscore, or dash with underscore
        safe_ticker = re.sub(r'[^A-Za-z0-9_\-]', '_', ticker)


        ticker_df.to_csv(output_dir / f"{safe_ticker}.csv", index=False)




if __name__ == '__main__':

    for file in paths.RAW_DATA.rglob("*.csv"):

        if file.is_file():

            # floor-2025-01-01.csv -> 2025-01-01
            date = file.stem.removeprefix("floor-")

            preprocess_raw_data(date)

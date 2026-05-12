from locale import normalize
from pathlib import Path
import pandas as pd
from datetime import date
import re
from src.utils.paths import RAW_DATA,PROCESSED_DATA,ARTIFACTS
import json


with open(ARTIFACTS / "allowed_symbols.json","r") as f:
    allowed_symbols = set(json.load(f));

    
def partiton_floorsheet_data(date = "2025-01-01"):

    input_file = RAW_DATA / f"floor-{date}.csv"
    output_dir = PROCESSED_DATA / date
    

    df = pd.read_csv(Path(input_file), engine="python")

    output_dir.mkdir(parents=True, exist_ok=True)

    df["transaction_time"] = df["transaction_time"].astype(str)

    #remove commas
    df["transaction_time"] = df["transaction_time"].str.replace(",", "", regex=False)

    # ix ms safely using function
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

    

    tickers = df[df["symbol"].isin(allowed_symbols)]
    tickers = df["symbol"].unique()

    for ticker in tickers:  

        ticker_df = df[df["symbol"] == ticker]

        # Replace any character that is not a letter, number, underscore, or dash with underscore
        safe_ticker = re.sub(r'[^A-Za-z0-9_\-]', '_', ticker)


        ticker_df.to_csv(output_dir / f"{safe_ticker}.csv", index=False)


def partition_all_floorsheet_data():

    for file in RAW_DATA.rglob("*.csv"):

        # if file.is_file() and file.stem.startswith("floor-2024"):
        if file.is_file():

            print(1)
            # floor-2025-01-01.csv -> 2025-01-01
            date = file.stem.removeprefix("floor-")

            partiton_floorsheet_data(date)



if(__name__ == '__main__') :
    partition_all_floorsheet_data()


from src.utils.io import get_symbols
from src.utils.paths import BASE_DIR
import pandas as pd
from pathlib import Path

def normalize_interday_columns(input) :

    symbols = get_symbols()

    output_dir = BASE_DIR / "AnomalyEngine" / "data"
    output_dir.mkdir(parents=True,exist_ok=True)
    
    for file in Path(input).glob("*.csv") :
        df = pd.read_csv(file)
        symbol = file.stem;

        if symbol not in symbols:
            continue

        df.rename(columns={
            "published_date":"date",
            "traded_quantity":"volume",
            "traded_amount":"amount"
        },inplace=True)

        df = df.drop(columns=["status", "per_change"],errors="ignore")

        cols = ["open", "high", "low", "close","volume", "amount"]
        df = df[df[cols].ne(0).all(axis=1)]
        

        df.to_csv(output_dir / f"{symbol}.csv",index=False)

if __name__ == "__main__":
    
    normalize_interday_columns(BASE_DIR / "company-wise")

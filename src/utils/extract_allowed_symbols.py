import pandas as pd
from src.utils import paths
import json


def get_symbols(folder):
    symbol_sets = []
    for file in folder.rglob("*.csv"):
        # print("Reading "+ file.name);
        df = pd.read_csv(file);
        symbols = set(df["symbol"].dropna().unique())
        symbol_sets.append(symbols)
    
    if not symbol_sets:
        return set()

    # * is the unpacking operator that breaks it down into multiple sets for intersection
    return set.intersection(*symbol_sets)

if __name__ == "__main__":
    allowed_symbols = get_symbols(paths.RAW_DATA)

    output_file = paths.ARTIFACTS / "allowed_symbols.json"
    paths.ARTIFACTS.mkdir(parents=True,exist_ok=True);
    
    with open(output_file,"w") as f:
        json.dump(sorted(list(allowed_symbols)), f, indent = 4)
    

import pandas as pd
import paths
import json


def get_symbols(folder):
    symbols = set()
    for file in folder.rglob("*.csv"):
        # print("Reading "+ file.name);
        df = pd.read_csv(file);
        symbols.update(df["symbol"].dropna().unique())

    return symbols

if __name__ == "__main__":
    allowed_symbols = get_symbols(paths.RAW_DATA)

    output_file = paths.CONFIG / "allowed_symbols.json"
    paths.DATA.mkdir(parents=True,exist_ok=True);
    
    with open(output_file,"w") as f:
        json.dump(sorted(list(allowed_symbols)), f, indent = 4)
    

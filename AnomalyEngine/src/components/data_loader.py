import pandas as pd
from src.utils.paths import DATA
from datetime import datetime


class DataLoader:
 
    def load(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        
        df = pd.read_csv(DATA / f"{symbol}.csv")
           
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if(start_date > end_date):
            raise ValueError("Start date must be before end date.")
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()

        df = df.loc[start_date:end_date]         

        # drop unnecessary columns
        df = df.drop(columns=["date"], errors="ignore")
        
        
        return df



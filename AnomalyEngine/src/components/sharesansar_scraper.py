import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from io import StringIO
import pandas as pd
from src.utils.paths import DATA
from src.utils import io
import warnings
warnings.filterwarnings("ignore")

class ShareSansarScraper:
    def __init__(self):
        self.base_url = 'https://www.sharesansar.com'
        self.ajax_url = f'{self.base_url}/ajaxtodayshareprice'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
        })

    def get_token(self):
        """Extract CSRF token from the main page"""
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        token_meta = soup.find('meta', {'name': '_token'})
        
        if token_meta:
            token = token_meta['content']
            return token
        else:
            return None

    def scrape(self, date):
        """Fetch share price data for a specific date"""
        token = self.get_token()
        if not token:
            print("Could not get CSRF token")
            return {
                "success": False,
                "date": date,
                "error": "Could not get CSRF token",
            }

        payload = {
            '_token': token,
            'sector': 'all_sec',
            'date': date
        }
                
        response = self.session.post(self.ajax_url, data=payload)

        print(response.text)
        return self.save_data(response.text)


    def save_data(self, html):
        bs = BeautifulSoup(html,"lxml")
        today = bs.select_one("span.text-org").text       

        updated_symbols = []
        created_symbols = []
        skipped_symbols = []

        #read html tables and convert to dataframe
        tables = pd.read_html(StringIO(html))

        #select the first table i.e the stock price table
        data_table = tables[0]


        for symbol in io.get_symbols():

            file = DATA / f"{symbol}.csv"

            data = data_table.loc[data_table["Symbol"] == symbol]

            if len(data) != 1:
                continue

            data_row = [[
                today,
                float(data["Open"].iloc[0]),
                float(data["High"].iloc[0]),
                float(data["Low"].iloc[0]),
                float(data["Close"].iloc[0]),
                float(data["Vol"].iloc[0]),
                float(data["Turnover"].iloc[0])
            ]]

            columns = [
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "amount"
            ]

            # File already exists
            if file.exists():

                existing_df = pd.read_csv(file)

                last_date = existing_df.iloc[-1]["date"]

                if str(last_date) >= str(today):
                    print(f"{symbol} already updated")
                    skipped_symbols.append(symbol)
                    continue

                print(f"Appending data for {symbol}")

                df = pd.DataFrame(data_row, columns=columns)

                df.to_csv(file, mode="a", header=False, index=False)
                updated_symbols.append(symbol)

            else:
                print(f"Creating file for {symbol}")

                df = pd.DataFrame(data_row, columns=columns)

                df.to_csv(file, index=False)
                created_symbols.append(symbol)

        return {
            "success": True,
            "date": today,
            "updated_count": len(updated_symbols),
            "created_count": len(created_symbols),
            "skipped_count": len(skipped_symbols),
            "updated_symbols": updated_symbols,
            "created_symbols": created_symbols,
            "skipped_symbols": skipped_symbols,
        }


if __name__ == '__main__':
    import sys
    
    # date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')

    date = '2026-05-22'
    
    scraper = ShareSansarScraper()
    scraper.scrape(date)
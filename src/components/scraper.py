"""
ShareHub Floorsheet Data Scraper
Scrapes daily floorsheet data from the widget URL by extracting embedded JSON
"""

import requests
import json
import pandas as pd
from datetime import datetime,timedelta
from pathlib import Path
import time
from typing import Optional, Dict, List
import logging
import re
import unicodedata
from src.utils.paths import PROJECT_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



def _normalize_api_date(date: Optional[str]) -> Optional[str]:
    """Return ISO YYYY-MM-DD for the floorsheet widget (server rejects unpadded parts)."""
    if date is None or not str(date).strip():
        return None
    raw = str(date).strip().replace("/", "-")
    parts = raw.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date (expected YYYY-MM-DD): {date!r}")
    y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    return f"{y:04d}-{m:02d}-{d:02d}"


def _sanitize_numeric_text(text: str) -> str:
    """Keep digits and separators only; normalize unicode punctuation."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = t.replace("\u00a0", "")
    t = re.sub(r"[^\d,.+-]", "", t)
    return t


def _collapse_grouping_dots(s: str) -> str:
    """Repeated '.' treated as grouping; last segment is fractional (e.g. '.354483.4' → '354483.4')."""
    if "." not in s:
        return s
    parts = s.split(".")
    if len(parts) <= 2:
        return s
    frac = parts[-1]
    int_joined = "".join(parts[:-1])
    if frac:
        return f"{int_joined}.{frac}" if int_joined else frac
    return int_joined or "0"


def _parse_decimal_cell(text: str) -> float:
    """
    Parse Western/Indian comma grouping, optional European decimal comma,
    or multiple dots from malformed table text.
    """
    s_full = _sanitize_numeric_text(text.strip())
    if not s_full:
        raise ValueError("empty numeric cell")
    negative = s_full.startswith("-")
    body = s_full[1:] if s_full.startswith(("+", "-")) else s_full
    ld = body.rfind(".")
    lc = body.rfind(",")
    decimal_is_comma = lc != -1 and lc > ld

    if decimal_is_comma:
        head, tail = body[:lc], body[lc + 1 :]
        integer_digits = "".join(ch for ch in head.replace(".", "").replace(",", "") if ch.isdigit())
        frac_digits = "".join(ch for ch in tail if ch.isdigit())
        mantissa_str = (integer_digits or "0") + ("." + frac_digits if frac_digits else "")
    else:
        mantissa_str = _collapse_grouping_dots(body.replace(",", ""))
    n = float(mantissa_str)
    return -n if negative else n


def _pagination_from_html_nav(html_content: str) -> Dict:
    """If RSC pagination is missing, infer whether Next page exists from DOM."""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")
        nav = soup.find("nav", attrs={"aria-label": re.compile("pagination", re.I)})
        if not nav:
            return {}
        for btn in nav.find_all("button"):
            if "Next" not in btn.get_text():
                continue
            return {"hasNext": not btn.has_attr("disabled")}
    except Exception:
        pass
    return {}


class FloorsheeetScraper:
    """Scraper for ShareHub floorsheet data from widget URL"""

    BASE_URL = "https://sharehubnepal.com/widgets/floorsheet-widget"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.data = []
    
    def get_floorsheet_data(self, page: int = 1, date: Optional[str] = None, 
                            page_size: int = 100) -> Optional[tuple]:
        """
        Fetch floorsheet data for a specific page and date
        
        Args:
            page: Page number (default 1)
            date: Date in format YYYY-M-DD (default today)
            page_size: Number of items per page (default 100)
        
        Returns:
            Tuple of (records_list, pagination_info) or (None, {}) if failed
        """
        try:
            if date is None:
                raise Exception("Date not defined");
            else:
                api_date = _normalize_api_date(date)

            params = {
                'Page': page,
                'date': api_date,
                'Size': page_size
            }
            
            logger.info(f"Fetching floorsheet data - Page: {page}, Date: {api_date}, Size: {page_size}")
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the embedded JSON data from Next.js response
            records, pagination_info = self._extract_json_from_html(response.text)
            
            if records:
                logger.info(f"Successfully retrieved {len(records)} records from page {page}")
            else:
                logger.warning(f"No records found on page {page}")
            
            return records, pagination_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from page {page}: {e}")
            return None, {}
    
    def _extract_json_from_html(self, html_content: str) -> tuple:
        """
        Extract floorsheet rows and pagination from Next.js RSC payload (floorSheetData),
        falling back to <tbody> parsing and UI pagination hints.
        """
        records = []
        pagination_info: Dict = {}

        try:

            logger.info("Scraping floorsheet data using HTML table")
            records = self._parse_html_table(html_content)
            ui = _pagination_from_html_nav(html_content)
            pagination_info = {
                "hasNext": ui.get("hasNext", False),
                "hasPrevious": False,
                "totalPages": 0,
                "pageIndex": 0,
                "totalTrades": 0,
                "totalItems": 0,
                "pageSize": 100,
                "totalAmount": 0,
                "totalQty": 0,
            }

        except Exception as e:
            logger.error(f"Error scrapping data: {e}")

        return records, pagination_info
    
    def _parse_html_table(self, html_content: str) -> List[Dict]:
        """
        Parse HTML table and extract floorsheet data
        
        Args:
            html_content: HTML content of the response
        
        Returns:
            List of floorsheet records
        """
        records = []
        
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the table body
            tbody = soup.find('tbody')
            
            if not tbody:
                logger.warning("Table body not found in HTML")
                return records
            
            # Get all table rows
            rows = tbody.find_all('tr')
            logger.info(f"Found {len(rows)} rows in HTML table")
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) >= 8:
                    try:
                        # Extract symbol from the first cell
                        # The cell contains: <span>Avatar</span> + symbol text
                        # We need to extract just the symbol part
                        symbol_cell = cells[0]
                        
                        # Try to get symbol from link first
                        link = symbol_cell.find('a')
                        if link:
                            symbol = link.get_text(strip=True)
                            if len(symbol) > 1 and symbol[0] == symbol[1]:
                                symbol = symbol[1:]
                        else:
                            # Fallback: get all text and remove avatar character
                            full_text = symbol_cell.get_text(strip=True)
                            # Remove the avatar character (first char) if it's repeated
                            # Pattern: if first char is repeated at start, remove one
                            symbol = full_text
                            if len(symbol) > 1 and symbol[0] == symbol[1]:
                                symbol = symbol[1:]
                        
                        # Extract numeric values
                        buyer_id = cells[1].get_text(strip=True)
                        seller_id = cells[2].get_text(strip=True)
                        quantity = int(round(_parse_decimal_cell(cells[3].get_text(strip=True))))
                        price = _parse_decimal_cell(cells[4].get_text(strip=True))
                        # Parsed amount strings are unreliable (lakhs shorthand, commas, stray dots).
                        amount = quantity * price
                        
                        trade_time = cells[6].get_text(strip=True)
                        contract_id = cells[7].get_text(strip=True)
                        
                        record = {
                            'symbol': symbol,
                            'buyer_member_id': buyer_id,
                            'seller_member_id': seller_id,
                            'volume': quantity,
                            'price': price,
                            'amount': amount,
                            'transaction_time': trade_time,
                            'contract_id': contract_id,
                        }
                        records.append(record)
                        
                    except (ValueError, IndexError, AttributeError) as e:
                        logger.warning(f"Error parsing row: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error parsing HTML table: {e}")
        
        return records
    
    def get_all_floorsheet_data(self, date: Optional[str] = None, 
                                max_pages: Optional[int] = None,
                                page_size: int = 100, delay: float = 0.5) -> List[Dict]:
        """
        Fetch all floorsheet data across multiple pages for a specific date
        
        Args:
            date: Date in format YYYY-M-DD (default today)
            max_pages: If set, stop after this many pages (for quick tests). None = keep going until a page has no rows.
            page_size: Number of items per page
            delay: Delay between requests in seconds
        
        Returns:
            List of all floorsheet records
        """
        all_records = []
        page = 1
        pagination_info: Dict = {}

        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break

            records, pagination_info = self.get_floorsheet_data(
                page=page, date=date, page_size=page_size
            )

            if records is None:
                logger.warning(f"Request failed for page {page}, stopping")
                break

            # Past last page (e.g. Page=1042 with totalPages=1041): API returns empty content / "No Data Found" table.
            if not records:
                logger.info(
                    f"No rows on page {page} — done (past last page or no floorsheet data for this date)"
                )
                break

            all_records.extend(records)
            logger.info(
                f"Page {page}: {len(records)} rows (running total {len(all_records)}; "
            )
            page += 1
            time.sleep(delay)
        
        logger.info(f"Total records collected: {len(all_records)}")
        logger.info(f"Final pagination info: Page {pagination_info.get('pageIndex', 'N/A')} of {pagination_info.get('totalPages', 'N/A')}")
        return all_records
    
    def save_to_csv(self, records: List[Dict], filename) -> str:
        """
        Save floorsheet data to CSV file
        
        Args:
            records: List of floorsheet records
            filename: Output filename (default: floorsheet_YYYYMMDD.csv)
        
        Returns:
            Path to saved file
        """
        if not records:
            logger.warning("No records to save")
            return ""
        
        
        
        df = pd.DataFrame(records)
        filepath = Path(filename)
        
        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Data saved to {filepath}")
            logger.info(f"Total rows: {len(df)}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return ""
    
    def save_to_json(self, records: List[Dict], filename) -> str:
        """
        Save floorsheet data to JSON file
        
        Args:
            records: List of floorsheet records
            filename: Output filename (default: floorsheet_YYYYMMDD.json)
        
        Returns:
            Path to saved file
        """
        if not records:
            logger.warning("No records to save")
            return ""
        
        
        
        filepath = Path(filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            return ""
    
    def save_to_excel(self, records: List[Dict], filename) -> str:
        """
        Save floorsheet data to Excel file
        
        Args:
            records: List of floorsheet records
            filename: Output filename (default: floorsheet_YYYYMMDD.xlsx)
        
        Returns:
            Path to saved file
        """
        if not records:
            logger.warning("No records to save")
            return ""
        
       
        
        df = pd.DataFrame(records)
        filepath = Path(filename)
        
        try:
            df.to_excel(filepath, index=False, sheet_name='Floorsheet')
            logger.info(f"Data saved to {filepath}")
            logger.info(f"Total rows: {len(df)}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving Excel: {e}")
            return ""
    
    def get_summary_stats(self, records: List[Dict]) -> Dict:
        """
        Calculate summary statistics from floorsheet data
        
        Args:
            records: List of floorsheet records
        
        Returns:
            Dictionary with summary statistics
        """
        if not records:
            return {}
        
        df = pd.DataFrame(records)
        
        stats = {
            'total_trades': len(df),
            'total_quantity': int(df['volume'].sum()),
            'total_amount': float(df['amount'].sum()),
            'average_price': float(df['price'].mean()),
            'average_quantity': float(df['volume'].mean()),
            'unique_symbols': int(df['symbol'].nunique()),
            'top_5_symbols': df['symbol'].value_counts().head(5).to_dict(),
            'top_5_by_volume': df.groupby('symbol')['volume'].sum().nlargest(5).to_dict(),
            'top_5_by_amount': df.groupby('symbol')['amount'].sum().nlargest(5).to_dict(),
        }
        
        return stats
    
    def run(self, date, max_pages: Optional[int] = None, 
            output_format: str = 'both') -> Dict:
        """
        Run the scraper and save results
        
        Args:
            date: Date in format YYYY-M-DD (default today)
            max_pages: Cap at N pages for testing; None = full day (stop on empty page)
            output_format: 'csv', 'json', 'excel', or 'all'
        
        Returns:
            Dictionary with results and file paths
        """
        logger.info("Starting floorsheet scraper")


        records = self.get_all_floorsheet_data(date=date, max_pages=max_pages,delay=0.01)
        
        if not records:
            logger.error("No data retrieved")
            return {'success': False, 'error': 'No data retrieved'}
        
        results = {
            'success': True,
            'records_count': len(records),
            'date': date,
            'files': {}
        }
        
        # Save files
        if output_format in ['csv', 'both', 'all']:
            csv_file = self.save_to_csv(
                records, filename=f"{PROJECT_ROOT}/data/raw/floor-{date}.csv"
            )
            if csv_file:
                results['files']['csv'] = csv_file
        
        if output_format in ['json', 'both', 'all']:
            json_file = self.save_to_json(
                records, filename=f"{PROJECT_ROOT}/data/raw/floor-{date}.json"
            )
            if json_file:
                results['files']['json'] = json_file
        
        if output_format in ['excel', 'all']:
            excel_file = self.save_to_excel(
                records, filename=f"{PROJECT_ROOT}/data/raw/floor-{date}.xlsx"
            )
            if excel_file:
                results['files']['excel'] = excel_file
        
        # Get statistics
        stats = self.get_summary_stats(records)
        results['statistics'] = stats
        
        logger.info(f"Scraper completed successfully")
        logger.info(f"Summary: {json.dumps(stats, indent=2, default=str)}")
        
        return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ShareHub Floorsheet Data Scraper')
    parser.add_argument('--date', type=str, default=None, 
                        help='Date in format YYYY-MM-DD (default: today)')
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        metavar='N',
        help='Only fetch the first N pages (default: fetch all pages until one is empty)',
    )
    parser.add_argument('--format', choices=['csv', 'json', 'excel', 'both', 'all'], 
                        default='csv', help='Output format')
    parser.add_argument('--page-size', type=int, default=100,
                        help='Items per page (default: 100)')
    
    args = parser.parse_args()

    # today = (
    #     datetime.now().strftime("%Y-%m-%d")
    #     if args.date is None
    #     else _normalize_api_date(args.date)
    # )


    start_scrape = datetime.strptime('2024-11-01',"%Y-%m-%d");
    end_scrape = datetime.strptime('2024-12-31',"%Y-%m-%d");


    

    while(start_scrape<=end_scrape):
        date = datetime.strftime(start_scrape,"%Y-%m-%d");
        print(f"Scraping floorsheet for {date} → floor-{date}.*")
        scraper = FloorsheeetScraper()
        results = scraper.run(
            date=date,
            max_pages=args.max_pages,
            output_format=args.format,
        )

        print("\n" + "="*60)
        print("SCRAPING RESULTS")
        print("="*60)
        print(json.dumps(results, indent=2, default=str))



        start_scrape += timedelta(days=1);


   


if __name__ == "__main__":
    main()
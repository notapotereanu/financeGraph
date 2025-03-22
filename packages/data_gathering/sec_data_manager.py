"""Helper module for SEC data management and filing processing."""

import time
from typing import Optional, Dict, Set, List
import pandas as pd
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from sec_api import QueryApi
from packages.helpers.InsiderTransaction import InsiderTransaction

# Disable pandas warnings
import warnings
warnings.filterwarnings('ignore')

# Constants
HEADERS = {
    "User-Agent": "MyScraper/1.0 (https://www.mywebsite.com/contact; contact@mywebsite.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

TRANSACTION_CODE_MAPPING = {
    "P": "Purchase",
    "S": "Sale",
    "F": "Gift",
    "M": "Exercise"
}

class SECDataManager:
    """Handles SEC data retrieval and processing."""
    
    def __init__(self, stock_ticker: str):
        """
        Initialize the SECDataManager.
        
        Args:
            stock_ticker: The stock ticker symbol to analyze
        """
        self.stock_ticker = stock_ticker
        self.sec_cik = self._get_sec_cik()
        self.sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.sec_cik}&type=4&dateb=&owner=exclude&count=100&search_text="
    
        
        
    def _get_sec_cik(self) -> str:
        """
        Get the SEC CIK code for the stock ticker using the sec-api package.
        
        Returns:
            str: The 10-digit CIK code with leading zeros
        """
        print(f"🔍 Looking up SEC CIK for {self.stock_ticker}...")
        try:
            queryApi = QueryApi("7afdb19cd4eab20201f2b2ef69710e460b1555d75a5a1fab271efb01d307fcfb")
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{self.stock_ticker}"
                    }
                },
                "from": "0",
                "size": "1",
                "sort": [{"filedAt": {"order": "desc"}}]
            }
            
            filings = queryApi.get_filings(query)
            if filings and len(filings) > 0:
                cik = filings.get('filings')[0].get('cik')
                if cik:
                    # Format CIK to 10 digits with leading zeros
                    formatted_cik = cik.zfill(10)
                    print(f"✅ Found CIK: {formatted_cik}")
                    return formatted_cik
            print("⚠️ No CIK found in SEC filings")
            return ""
        except Exception as e:
            print(f"❌ Error getting SEC CIK: {e}")
            return ""
    
    def _get_sec_interal_people(self) -> List[Dict]:
        """
        Get directors and board members from SEC API.
        
        Returns:
            List of dictionaries containing insider information
        """
        print("🔍 Looking up SEC internal people...")
        try:
            queryApi = QueryApi("7afdb19cd4eab20201f2b2ef69710e460b1555d75a5a1fab271efb01d307fcfb")
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{self.stock_ticker} AND formType:\"DEF 14A\""
                    }
                },
                "from": "0",
                "size": "1",
                "sort": [{"filedAt": {"order": "desc"}}]
            }
            
            filings = queryApi.get_filings(query)
            if filings and len(filings) > 0:
                filing = filings[0]
                directors = filing.get('directors', [])
                officers = filing.get('officers', [])
                
                people = []
                for director in directors:
                    people.append({
                        'name': director.get('name', ''),
                        'title': 'Director',
                        'cik': director.get('cik', '')
                    })
                for officer in officers:
                    people.append({
                        'name': officer.get('name', ''),
                        'title': officer.get('title', 'Officer'),
                        'cik': officer.get('cik', '')
                    })
                
                print(f"✅ Found {len(people)} internal people")
                return people
            print("⚠️ No internal people found in SEC filings")
            return []
        except Exception as e:
            print(f"❌ Error getting SEC internal people: {e}")
            return []
    
    def get_insider_holdings(self, sec_df: pd.DataFrame) -> Dict[str, Set[str]]:
        """
        Get stocks owned by insiders based on SEC filings.
        
        Args:
            sec_df: DataFrame containing SEC transactions
            
        Returns:
            Dictionary mapping insider names to sets of stock tickers they own
        """
        print("🔍 Analyzing insider holdings...")
        try:
            insider_holdings = {}
            
            # Get internal people from SEC
            internal_people = self._get_sec_interal_people()
            internal_names = {person['name'] for person in internal_people}
            
            # Process SEC transactions
            for _, row in sec_df.iterrows():
                insider_name = row['insider_name']
                if insider_name in internal_names:
                    if insider_name not in insider_holdings:
                        insider_holdings[insider_name] = set()
                    insider_holdings[insider_name].add(row['stock_ticker'])
            
            print(f"✅ Found holdings for {len(insider_holdings)} insiders")
            return insider_holdings
        except Exception as e:
            print(f"❌ Error getting insider holdings: {e}")
            return {}
    
    def get_sec_filings(self) -> pd.DataFrame:
        """
        Get SEC Form 4 filings for the stock.
        
        Returns:
            DataFrame containing processed SEC filings
        """
        print("🔍 Fetching SEC Form 4 filings...")
        try:
            filings = self._scrape_sec_filings(self.sec_url)
            insider_transactions = []
            
            for filing in filings:
                txn_obj = InsiderTransaction(
                    detail_url=filing.get("detail_url"),
                    issuerTradingSymbol=filing.get("issuerTradingSymbol"),
                    insider_name=filing.get("insider_name"),
                    insider_cik=filing.get("insider_cik"),
                    relationship=filing.get("relationship"),
                    transactions=filing.get("transactions"),
                    xml_link=filing.get("xml_link")
                )
                insider_transactions.append(txn_obj)
            
            sec_transactions_flat_data = self._flatten_transactions(insider_transactions)
            sec_df = pd.DataFrame(sec_transactions_flat_data, columns=[
                'date', 'stock_ticker', 'issuerTradingSymbol', 'price', 'insider_name', 'insider_cik', 'relationship',
                'transaction_type', 'shares', 'value', 'shares_total', 'xml_link'
            ])
            sec_df = self._clean_data(sec_df)
            
            print(f"✅ Successfully processed {len(sec_df)} SEC filings")
            return sec_df
        except Exception as e:
            print(f"❌ Error getting SEC filings: {e}")
            return pd.DataFrame()
    
    def _parse_form4_xml(self, xml_content: bytes, detail_url: str, xml_link: str) -> Optional[Dict]:
        """
        Parse the Form 4 XML content and extract insider trading details.
        
        Args:
            xml_content: Raw XML content
            detail_url: URL of the filing detail page
            xml_link: URL of the XML file
            
        Returns:
            Dictionary containing parsed filing data or None if parsing fails
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            print(f"Error parsing XML from {xml_link}: {e}")
            return None

        # Extract Insider Name
        insider_name = ""
        name_elem = root.find(".//reportingOwner/reportingOwnerId/rptOwnerName")
        if name_elem is not None and name_elem.text:
            insider_name = name_elem.text.strip()

        insider_cik = ""
        name_elem = root.find(".//reportingOwner/reportingOwnerId/rptOwnerCik")
        if name_elem is not None and name_elem.text:
            insider_cik = name_elem.text.strip()
            
        issuerTradingSymbol = ""
        name_elem = root.find(".//issuer/issuerTradingSymbol")
        if name_elem is not None and name_elem.text:
            issuerTradingSymbol = name_elem.text.strip()
            
        # Extract Relationship
        relationship = ""
        rel_elem = root.find(".//reportingOwner/reportingOwnerRelationship")
        if rel_elem is not None:
            parts = []
            if rel_elem.findtext("isDirector") == "1":
                parts.append("Director")
            if rel_elem.findtext("isOfficer") == "1":
                officer_title = rel_elem.findtext("officerTitle") or ""
                parts.append(f"Officer ({officer_title.strip()})" if officer_title.strip() else "Officer")
            if rel_elem.findtext("isTenPercentOwner") == "1":
                parts.append("10% Owner")
            if rel_elem.findtext("isOther") == "1":
                parts.append("Other")
            relationship = ", ".join(parts)

        # Extract Transaction Details
        transactions = []
        for txn in root.findall(".//nonDerivativeTable/nonDerivativeTransaction"):
            txn_date = txn.findtext(".//transactionDate/value")
            raw_txn_code = txn.findtext(".//transactionCoding/transactionCode")
            txn_type = TRANSACTION_CODE_MAPPING.get(raw_txn_code, raw_txn_code)
            cost = txn.findtext(".//transactionAmounts/transactionPricePerShare/value")
            shares = txn.findtext(".//transactionAmounts/transactionShares/value")
            try:
                computed_value = float(cost) * float(shares)
                computed_value = round(computed_value, 2)
            except Exception:
                computed_value = ""
            shares_total = txn.findtext(".//postTransactionAmounts/sharesOwnedFollowingTransaction/value")
            transactions.append({
                "date": txn_date,
                "transaction_type": txn_type,
                "cost": cost,
                "shares": shares,
                "value": str(computed_value),
                "shares_total": shares_total
            })

        return {
            "detail_url": detail_url,
            "issuerTradingSymbol": issuerTradingSymbol,
            "insider_name": insider_name,
            "insider_cik": insider_cik,
            "relationship": relationship,
            "transactions": transactions,
            "xml_link": xml_link
        }
    
    def _scrape_filing_detail(self, detail_url: str) -> Optional[Dict]:
        """
        Scrape an individual Form 4 filing detail page.
        
        Args:
            detail_url: URL of the filing detail page
            
        Returns:
            Dictionary containing filing data or None if scraping fails
        """
        try:
            response = requests.get(detail_url, headers=HEADERS)
            response.raise_for_status()
        except Exception as e:
            print(f"Error scraping detail page {detail_url}: {e}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the XML link
        xml_link = ""
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.xml'):
                possible_xml_url = "https://www.sec.gov" + href
                try:
                    head_response = requests.head(possible_xml_url, headers=HEADERS)
                    content_type = head_response.headers.get('Content-Type', '')
                    if 'xml' in content_type.lower():
                        xml_link = possible_xml_url
                        break
                except Exception as e:
                    print(f"Error checking URL {possible_xml_url}: {e}")

        if not xml_link:
            print(f"No XML link found for {detail_url}")
            return None

        # Fetch the XML content
        try:
            xml_response = requests.get(xml_link, headers=HEADERS, timeout=30)
            xml_response.raise_for_status()
            xml_content = xml_response.content
        except requests.Timeout:
            print(f"Timeout while fetching XML content from {xml_link}")
            return None
        except Exception as e:
            print(f"Error fetching XML content from {xml_link}: {e}")
            return None

        # Parse the XML and extract desired data
        filing_data = self._parse_form4_xml(xml_content, detail_url, xml_link)
        return filing_data
    
    def _scrape_sec_filings(self, url: str) -> List[Dict]:
        """
        Scrape the SEC Form 4 filings list page.
        
        Args:
            url: URL of the SEC filings list page
            
        Returns:
            List of dictionaries containing filing data
        """
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
        except Exception as e:
            print(f"Error scraping list page: {e}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        filings = []

        # Look for rows that include a link to the filing detail page
        for row in soup.find_all('tr'):
            link_tag = row.find('a', href=True)
            if link_tag and 'Archives' in link_tag['href']:
                detail_url = "https://www.sec.gov" + link_tag['href']
                print(f"🔹 Processing filing detail page: {detail_url}")
                filing_data = self._scrape_filing_detail(detail_url)
                if filing_data:
                    filings.append(filing_data)
                # Pause to respect SEC rate limiting guidelines
                time.sleep(0.5)
        return filings
    
    def _flatten_transactions(self, insider_transactions: List[InsiderTransaction]) -> List[Dict]:
        """
        Flatten InsiderTransaction objects into a list of dictionaries.
        
        Args:
            insider_transactions: List of InsiderTransaction objects
            
        Returns:
            List of dictionaries containing flattened transaction data
        """
        rows = []
        for it in insider_transactions:
            for txn in it.transactions:
                row = {
                    'date': txn['date'],
                    'stock_ticker': self.stock_ticker,
                    'issuerTradingSymbol': it.issuerTradingSymbol,
                    'price': txn['cost'],
                    'insider_name': it.insider_name,
                    'insider_cik': it.insider_cik,
                    'relationship': it.relationship,
                    'transaction_type': txn['transaction_type'],
                    'shares': txn['shares'],
                    'value': txn['value'],
                    'shares_total': txn['shares_total'],
                    'xml_link': it.xml_link
                }
                rows.append(row)
        return rows
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the DataFrame.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        # Remove rows with transaction_type "Gift" or "Exercise"
        df = df[~df['transaction_type'].isin(['Gift', 'Exercise'])]
        
        # Convert price column to numeric and remove rows where price is 0
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[df['price'] != 0]
        
        # Fill in empty stock_ticker values with issuerTradingSymbol where available
        df.loc[df['stock_ticker'].isna() & df['issuerTradingSymbol'].notna(), 'stock_ticker'] = df.loc[df['stock_ticker'].isna() & df['issuerTradingSymbol'].notna(), 'issuerTradingSymbol']
        
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        except Exception as e:
            print(f"Error converting dates: {e}")
            
        return df 
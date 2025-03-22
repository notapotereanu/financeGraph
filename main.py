"""Main module for financial data analysis and RDF storage."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set

import pandas as pd
import yfinance as yf

from packages.finviz import get_finviz_ratings
from packages.googleAPI import googleAPI_get_df
from packages.newsAPI import newsAPI_get_df
from packages.secFillings import get_sec_fillings
from packages.tripleStoreStorage import TripleStoreStorage
from config import (
    TRIPLESTORE_ENDPOINT,
    SPARQL_QUERY_ENDPOINT,
    ONTOLOGY_PATH,
    DEFAULT_STOCK_TICKER,
    DEFAULT_NEWS_ARTICLES,
    DEFAULT_STOCK_HISTORY_DAYS
)
from queries import get_sparql_queries


class FinancialDataAnalyzer:
    """Main class for financial data analysis and RDF storage."""

    def __init__(self, stock_ticker: str = DEFAULT_STOCK_TICKER):
        """
        Initialize the FinancialDataAnalyzer.
        
        Args:
            stock_ticker: The stock ticker symbol to analyze
        """
        self.stock_ticker = stock_ticker
        self.sec_cik = self._get_sec_cik()
        if not self.sec_cik:
            raise ValueError(f"Failed to get SEC CIK for {stock_ticker}")
        
        self.sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.sec_cik}&type=4&owner=only&count=100"
        self.storage = TripleStoreStorage(TRIPLESTORE_ENDPOINT, SPARQL_QUERY_ENDPOINT)

    def _get_sec_cik(self) -> Optional[str]:
        """
        Get the SEC CIK number for the stock ticker.
        
        Returns:
            The CIK as a string with leading zeros, or None if not found
        """
        try:
            company = yf.Ticker(self.stock_ticker)
            info = company.info
            cik = str(info.get('cik', ''))
            return cik.zfill(10)
        except Exception as e:
            print(f"❌ Error getting SEC CIK for {self.stock_ticker}: {e}")
            return None

    def _get_insider_holdings(self, sec_df: pd.DataFrame) -> Dict[str, Set[str]]:
        """
        Get all stocks that each insider owns based on SEC filings.
        
        Args:
            sec_df: DataFrame containing SEC filing data
            
        Returns:
            Dictionary mapping insider names to sets of stock tickers they own
        """
        print("🔹 Gathering Insider Holdings ...")
        try:
            insider_holdings: Dict[str, Set[str]] = {}
            
            # Group by insider name and get unique stock tickers
            for insider_name in sec_df['insider_name'].unique():
                insider_data = sec_df[sec_df['insider_name'] == insider_name]
                holdings = set(insider_data['stock_ticker'].unique())
                insider_holdings[insider_name] = holdings
            
            print(f"✅ Found holdings for {len(insider_holdings)} insiders")
            return insider_holdings
        except Exception as e:
            print(f"❌ Error gathering insider holdings: {e}")
            raise

    def load_ontology(self) -> bool:
        """
        Load the ontology file into the triplestore.
        
        Returns:
            True if successful, False otherwise
        """
        if os.path.exists(ONTOLOGY_PATH):
            self.storage.load_ontology(ONTOLOGY_PATH)
            print("✅ Ontology successfully loaded.")
            return True
        print("⚠️ Ontology file not found. Make sure `finance.owl` is in the correct path.")
        return False

    def gather_data(self) -> Dict[str, Any]:
        """
        Gather all required financial data.
        
        Returns:
            Dictionary containing all gathered dataframes and insider holdings
        """
        print("🔹 Gathering Data ...")
        try:
            sec_df = get_sec_fillings(self.sec_url, self.stock_ticker)
            insider_holdings = self._get_insider_holdings(sec_df)
            
            data = {
                'sec_transactions': sec_df,
                'google_trends': googleAPI_get_df([self.stock_ticker]),
                'news_sentiment': newsAPI_get_df(self.stock_ticker, num_articles=DEFAULT_NEWS_ARTICLES),
                'analysts_ratings': get_finviz_ratings(self.stock_ticker),
                'stock_data': yf.download(
                    self.stock_ticker,
                    start=datetime.today() - timedelta(days=DEFAULT_STOCK_HISTORY_DAYS),
                    end=datetime.today()
                ),
                'insider_holdings': insider_holdings
            }
            print("✅ Data successfully gathered.")
            return data
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            raise

    def store_data(self, data: Dict[str, Any]) -> None:
        """
        Convert and store data in the triplestore.
        
        Args:
            data: Dictionary containing all dataframes and insider holdings to store
        """
        print("🔹 Converting and Storing RDF Data ...")
        try:
            rdf_data = {
                'sec': self.storage.convert_sec_transactions_to_rdf(data['sec_transactions']),
                'google': self.storage.convert_google_trends_to_rdf(data['google_trends']),
                'news': self.storage.convert_news_sentiment_to_rdf(data['news_sentiment']),
                'analysts': self.storage.convert_analysts_ratings_to_rdf(data['analysts_ratings']),
                'stock': self.storage.convert_stock_data_to_rdf(data['stock_data']),
                'insider_holdings': self.storage.convert_insider_holdings_to_rdf(data['insider_holdings'])
            }

            for rdf in rdf_data.values():
                self.storage.store(rdf)

            print("✅ RDF data successfully stored in the triplestore.")
        except Exception as e:
            print(f"❌ Error converting or storing RDF data: {e}")
            raise

    def query_data(self) -> None:
        """Execute SPARQL queries and display results."""
        print("🔹 Querying the Triplestore ...")
        try:
            queries = get_sparql_queries(self.stock_ticker)
            
            for query_name, sparql_query in queries.items():
                print(f"\n🔎 Running Query: {query_name}")
                results = self.storage.query(sparql_query)
                
                if results and "results" in results:
                    for result in results["results"]["bindings"]:
                        print(result)
                else:
                    print("⚠️ No results found.")
        except Exception as e:
            print(f"❌ Error executing SPARQL query: {e}")
            raise

    def run_analysis(self) -> None:
        """Run the complete financial data analysis pipeline."""
        try:
            if not self.load_ontology():
                return

            data = self.gather_data()
            self.store_data(data)
            self.query_data()
        except Exception as e:
            print(f"❌ Error in analysis pipeline: {e}")
            raise


def main():
    """Main entry point for the application."""
    try:
        analyzer = FinancialDataAnalyzer()
        analyzer.run_analysis()
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

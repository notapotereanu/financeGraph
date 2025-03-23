"""Main module for financial data analysis and RDF storage."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
import time
import json

import pandas as pd
import yfinance as yf

# Disable pandas warnings
import warnings
warnings.filterwarnings('ignore')

from packages.data_gathering.competitors import get_competitors
from packages.data_gathering.finviz import get_finviz_ratings
from packages.data_gathering.googleAPI import googleAPI_get_df
from packages.data_gathering.newsAPI import newsAPI_get_df
from packages.data_gathering.tripleStoreStorage import TripleStoreStorage
from packages.data_gathering.sec_data_manager import SECDataManager
from packages.helpers.data_analyzer import DataAnalyzer
from config import (
    TRIPLESTORE_ENDPOINT,
    SPARQL_QUERY_ENDPOINT,
    ONTOLOGY_PATH,
    DEFAULT_STOCK_TICKER,
    DEFAULT_NEWS_ARTICLES,
    DEFAULT_STOCK_HISTORY_DAYS
)
from packages.data_analyser.queries import get_sparql_queries


class FinancialDataAnalyzer:
    """Main class for financial data analysis and RDF storage."""

    def __init__(self, stock_ticker: str = DEFAULT_STOCK_TICKER):
        """
        Initialize the FinancialDataAnalyzer.
        
        Args:
            stock_ticker: The stock ticker symbol to analyze
        """
        self.stock_ticker = stock_ticker
        self.sec_manager = SECDataManager(stock_ticker)
        self.storage = TripleStoreStorage(TRIPLESTORE_ENDPOINT, SPARQL_QUERY_ENDPOINT)
        self.analyzer = DataAnalyzer(stock_ticker, self.storage)

    def gather_data(self) -> Dict[str, Any]:
        """
        Gather all required financial data.
        First tries to load from CSV files, then fetches fresh data if needed.
        
        Returns:
            Dictionary containing all gathered dataframes and insider holdings
        """
        print("🔹 Gathering Data ...")
        try:
            #sec_df = self.sec_manager.get_sec_filings()
            sec_df = pd.read_csv('sec_df.csv')
            #insider_holdings = self.sec_manager.get_insider_holdings(sec_df)
            with open('insider_holdings.json', 'r') as f:
                insider_holdings = json.load(f)
                
            unique_tickers = self.extractAllTickersFromInsiderHolding(insider_holdings)
            insider_stocks_data = self.downloadAllInsiderHoldingStockTrends(unique_tickers)
            
            ticker_info = yf.Ticker(self.stock_ticker).info
            data = {
                'sec_transactions': sec_df,
                'insider_holdings': insider_holdings,
                'insider_stocks_data': insider_stocks_data,
                'google_trends': googleAPI_get_df([self.stock_ticker]),
                'news_sentiment': newsAPI_get_df(self.stock_ticker, num_articles=DEFAULT_NEWS_ARTICLES),
                'analysts_ratings': get_finviz_ratings(self.stock_ticker),
                'stock_data': yf.download(
                    self.stock_ticker,
                    start=datetime.today() - timedelta(days=DEFAULT_STOCK_HISTORY_DAYS),
                    end=datetime.today()
                ),
                'company_officers' : self.sec_manager.get_board_members(),
                'company_description': ticker_info.get('longBusinessSummary', []),
                'company_name': ticker_info.get('displayName', []),
                'institutional_holders': yf.Ticker(self.stock_ticker).institutional_holders,
                'competitors': get_competitors(self.stock_ticker)
            }
            
            print("✅ Data successfully gathered.")
            return data
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            raise

    def downloadAllInsiderHoldingStockTrends(self, unique_tickers):
        insider_stocks_data = {}
        for ticker in unique_tickers:
            try:
                stock_data = yf.download(
                        ticker,
                        start=datetime.today() - timedelta(days=DEFAULT_STOCK_HISTORY_DAYS),
                        end=datetime.today()
                    )
                if not stock_data.empty:
                    # Reset index to make Date a column
                    stock_data = stock_data.reset_index()
                    # Rename the index column to 'Date'
                    stock_data = stock_data.rename(columns={'Date': 'Date'})
                    # Flatten multi-index columns by taking first level
                    stock_data.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data.columns]
                    # Set Date back as index
                    stock_data = stock_data.set_index('Date')
                    insider_stocks_data[ticker] = stock_data
            except Exception as e:
                print(f"❌ Error fetching data for {ticker}: {e}")
                continue
        return insider_stocks_data

    def extractAllTickersFromInsiderHolding(self, insider_holdings):
        unique_tickers = set()
        for insider_data in insider_holdings.values():
            if isinstance(insider_data, pd.DataFrame):
                unique_tickers.update(insider_data['issuerTradingSymbol'].unique())
            elif isinstance(insider_data, list):
                unique_tickers.update(entry['issuerTradingSymbol'] for entry in insider_data)
        return unique_tickers

    def run_analysis(self) -> None:
        """Run the complete financial data analysis pipeline."""
        try:
            #if not self.analyzer.load_ontology():
            #    return
            self.analyzer.store_data(self.gather_data())
            self.analyzer.query_data()
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

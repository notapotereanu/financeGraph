"""Main module for financial data analysis and RDF storage."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import os

import pandas as pd
import yfinance as yf

import warnings
warnings.filterwarnings('ignore')

from packages.data_gathering.competitors import get_competitors
from packages.data_gathering.finviz import get_finviz_ratings
from packages.data_gathering.googleAPI import googleAPI_get_df
from packages.data_gathering.newsAPI import newsAPI_get_df
from packages.data_gathering.sec_data_manager import SECDataManager
from config import (
    DEFAULT_STOCK_TICKER,
    DEFAULT_NEWS_ARTICLES,
    DEFAULT_STOCK_HISTORY_DAYS
)


class FinancialDataAnalyzer:
    """Main class for financial data analysis and RDF storage."""

    def __init__(self, stock_tickers: Optional[list] = None):
        """
        Initialize the FinancialDataAnalyzer.
        
        Args:
            stock_tickers: A list of stock ticker symbols to analyze
        """
        self.ticker = DEFAULT_STOCK_TICKER
        self.sec_manager = SECDataManager(self.ticker)

    def gather_data(self) ->  Dict[str, Any]:
        """
        Gather all required financial data for each ticker.
        First tries to load from CSV or JSON files, then fetches fresh data if needed.
        
        Returns:
            Dictionary containing all gathered dataframes and insider holdings for each ticker
        """
        print("🔹 Gathering Data ...")
        try:
            data = {}
            ticker_dir = os.path.join('data', self.ticker)
            if not os.path.exists(ticker_dir):
                os.makedirs(ticker_dir)

            # Check for existing files and load them if available
            sec_transactions_path = os.path.join(ticker_dir, 'sec_transactions.csv')
            insider_holdings_path = os.path.join(ticker_dir, 'insider_holdings')
            insider_stocks_data_path = os.path.join(ticker_dir, 'insider_stocks_data.json')
            google_trends_path = os.path.join(ticker_dir, 'google_trends.csv')
            news_sentiment_path = os.path.join(ticker_dir, 'news_sentiment.csv')
            analysts_ratings_path = os.path.join(ticker_dir, 'analysts_ratings.csv')
            stock_data_path = os.path.join(ticker_dir, 'stock_data.csv')
            company_officers_path = os.path.join(ticker_dir, 'company_officers.json')
            company_description_path = os.path.join(ticker_dir, 'company_description.json')
            company_name_path = os.path.join(ticker_dir, 'company_name.json')
            institutional_holders_path = os.path.join(ticker_dir, 'institutional_holders.csv')
            competitors_path = os.path.join(ticker_dir, 'competitors.json')

            if os.path.exists(sec_transactions_path):
                data['sec_transactions'] = pd.read_csv(sec_transactions_path)
            else:
                data['sec_transactions'] = self.sec_manager.get_sec_filings()
                #data['sec_transactions'] = pd.read_csv('sec_df.csv')

            if os.path.exists(insider_holdings_path):
                data['insider_holdings'] = {}
                insider_holdings_dir = os.path.join(ticker_dir, 'insider_holdings')
                if os.path.exists(insider_holdings_dir):
                    for insider_name in os.listdir(insider_holdings_dir):
                        insider_dir = os.path.join(insider_holdings_dir, insider_name)
                        if os.path.isdir(insider_dir):
                            holdings_file = os.path.join(insider_dir, 'holdings.csv')
                            if os.path.exists(holdings_file):
                                data['insider_holdings'][insider_name] = pd.read_csv(holdings_file)
            else:
                data['insider_holdings'] = self.sec_manager.get_insider_holdings(data['sec_transactions'])
                # Save each insider's holdings to a separate directory
                for insider_name, holdings_df in data['insider_holdings'].items():
                    insider_dir = os.path.join(insider_holdings_dir, insider_name)
                    if not os.path.exists(insider_dir):
                        os.makedirs(insider_dir)
                    holdings_file = os.path.join(insider_dir, 'holdings.csv')
                    holdings_df.to_csv(holdings_file, index=False)

            insider_stocks_data_dir = os.path.join(ticker_dir, 'insider_stocks_data')
            if os.path.exists(insider_stocks_data_path):
                data['insider_stocks_data'] = {}
                if os.path.exists(insider_stocks_data_dir):
                    for stock_file in os.listdir(insider_stocks_data_dir):
                        stock_path = os.path.join(insider_stocks_data_dir, stock_file)
                        if os.path.isfile(stock_path) and stock_file.endswith('.csv'):
                            stock_ticker = os.path.splitext(stock_file)[0]  # Get the ticker from the filename
                            data['insider_stocks_data'][stock_ticker] = pd.read_csv(stock_path)
            else:
                unique_tickers = self.extractAllTickersFromInsiderHolding(data['insider_holdings'])
                data['insider_stocks_data'] = self.downloadAllInsiderHoldingStockTrends(unique_tickers.keys())
                # Save each stock's data to a separate file
                for stock_ticker, stock_df in data['insider_stocks_data'].items():
                    stock_file = os.path.join(insider_stocks_data_dir, f'{stock_ticker}.csv')
                    stock_df.to_csv(stock_file, index=False)

            if os.path.exists(google_trends_path):
                data['google_trends'] = pd.read_csv(google_trends_path)
            else:
                data['google_trends'] = googleAPI_get_df([self.ticker])

            if os.path.exists(news_sentiment_path):
                data['news_sentiment'] = pd.read_csv(news_sentiment_path)
            else:
                data['news_sentiment'] = newsAPI_get_df(self.ticker, num_articles=DEFAULT_NEWS_ARTICLES)

            if os.path.exists(analysts_ratings_path):
                data['analysts_ratings'] = pd.read_csv(analysts_ratings_path)
            else:
                data['analysts_ratings'] = get_finviz_ratings(self.ticker)

            if os.path.exists(stock_data_path):
                data['stock_data'] = pd.read_csv(stock_data_path)
            else:
                data['stock_data'] = yf.download(
                    self.ticker,
                    start=datetime.today() - timedelta(days=DEFAULT_STOCK_HISTORY_DAYS),
                    end=datetime.today()
                )

            if os.path.exists(company_officers_path):
                with open(company_officers_path, 'r') as f:
                    data['company_officers'] = json.load(f)
            else: 
                data['company_officers'] = self.sec_manager.get_board_members()

            if os.path.exists(company_description_path):
                with open(company_description_path, 'r') as f:
                    data['company_description'] = json.load(f)
            else:
                ticker_info = yf.Ticker(self.ticker).info
                data['company_description'] = ticker_info.get('longBusinessSummary', [])

            if os.path.exists(company_name_path):
                with open(company_name_path, 'r') as f:
                    data['company_name'] = json.load(f)
            else:
                ticker_info = yf.Ticker(self.ticker).info
                data['company_name'] = ticker_info.get('displayName', [])

            if os.path.exists(institutional_holders_path):
                data['institutional_holders'] = pd.read_csv(institutional_holders_path)
            else:
                data['institutional_holders'] = yf.Ticker(self.ticker).institutional_holders[['Holder', 'Shares']]

            if os.path.exists(competitors_path):
                with open(competitors_path, 'r') as f:
                    data['competitors'] = json.load(f)
            else:
                data['competitors'] = get_competitors(self.ticker)


            print("✅ Data successfully gathered for all tickers.")
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
                    stock_data = stock_data.reset_index()
                    stock_data = stock_data.rename(columns={'Date': 'Date'})
                    stock_data.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data.columns]
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
        
        # Create dictionary mapping tickers to company names
        ticker_names = {}
        for ticker in unique_tickers:
            try:
                company_info = yf.Ticker(ticker).info
                company_name = company_info.get('longName') or company_info.get('shortName')
                if company_name:
                    ticker_names[ticker] = company_name
            except:
                continue
                
        return ticker_names

    def save_data(self, data:Dict[str, Any], base_directory: str = 'data') -> None:
        """
        Save the gathered data into JSON or CSV files for each ticker.

        Args:
            all_data: The dictionary containing all gathered data for each ticker.
            base_directory: The base directory where files will be saved.
        """
        import os
            
        directory = os.path.join(base_directory, self.ticker)
        if not os.path.exists(directory):
            os.makedirs(directory)

        for key, value in data.items():
            if key == 'insider_holdings' and isinstance(value, dict):
                insider_dir = os.path.join(directory, 'insider_holdings')
                if not os.path.exists(insider_dir):
                    os.makedirs(insider_dir)
                for insider_key, insider_df in value.items():
                    insider_subdir = os.path.join(insider_dir, insider_key)
                    if not os.path.exists(insider_subdir):
                        os.makedirs(insider_subdir)
                    holdings_path = os.path.join(insider_subdir, 'holdings.csv')
                    insider_df.to_csv(holdings_path, index=False)
            elif key == 'insider_stocks_data' and isinstance(value, dict):
                stocks_dir = os.path.join(directory, 'insider_stocks_data')
                if not os.path.exists(stocks_dir):
                    os.makedirs(stocks_dir)
                for stock_ticker, stock_df in value.items():
                    stock_path = os.path.join(stocks_dir, f'{stock_ticker}.csv')
                    stock_df.to_csv(stock_path)
            else:
                file_path = os.path.join(directory, f'{key}')
                if isinstance(value, pd.DataFrame):
                    file_path += '.csv'
                    value.to_csv(file_path, index=False)
                elif isinstance(value, (dict, list)):
                    file_path += '.json'
                    with open(file_path, 'w') as f:
                        json.dump(value, f, indent=4)
                elif isinstance(value, str):
                    file_path += '.txt'
                    with open(file_path, 'w') as f:
                        f.write(value)
                else:
                    print(f"Unsupported data type for key: {key}")

        print(f"✅ Data successfully saved for all tickers in {base_directory}.")

    def run_analysis(self) -> None:
        """Run the complete financial data analysis pipeline for all tickers."""
        try:
            all_data = self.gather_data()
            self.save_data(all_data)
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

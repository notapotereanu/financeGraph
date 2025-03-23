from datetime import datetime, timedelta
from typing import Dict, Any
import os
import pandas as pd
import yfinance as yf
import json

from packages.data_gathering.googleAPI import googleAPI_get_df
from packages.data_gathering.newsAPI import newsAPI_get_df
from packages.data_gathering.finviz import get_finviz_ratings
from packages.data_gathering.sec_data_manager import SECDataManager
from packages.data_gathering.competitors import get_competitors
from config import DEFAULT_NEWS_ARTICLES, DEFAULT_STOCK_HISTORY_DAYS

class DataGatherer:
    def __init__(self, ticker: str, sec_manager: SECDataManager):
        self.ticker = ticker
        self.sec_manager = sec_manager

    def gather_data(self) -> Dict[str, Any]:
        print("🔹 Gathering Data ...")
        try:
            data = {}
            ticker_dir = os.path.join('data', self.ticker)
            if not os.path.exists(ticker_dir):
                os.makedirs(ticker_dir)

            # Check for existing files and load them if available
            sec_transactions_path = os.path.join(ticker_dir, 'sec_transactions.csv')
            insider_holdings_dir = os.path.join(ticker_dir, 'insider_holdings')
            insider_stocks_data_dir = os.path.join(ticker_dir, 'insider_stocks_data')
            google_trends_path = os.path.join(ticker_dir, 'google_trends.csv')
            news_sentiment_path = os.path.join(ticker_dir, 'news_sentiment.csv')
            analysts_ratings_path = os.path.join(ticker_dir, 'analysts_ratings.csv')
            stock_data_path = os.path.join(ticker_dir, 'stock_data.csv')
            company_officers_path = os.path.join(ticker_dir, 'company_officers.csv')
            company_description_path = os.path.join(ticker_dir, 'company_description.txt')
            company_name_path = os.path.join(ticker_dir, 'company_name.txt')
            institutional_holders_path = os.path.join(ticker_dir, 'institutional_holders.csv')
            competitors_path = os.path.join(ticker_dir, 'competitors.json')
            data['insider_holdings'] = {}

            if os.path.exists(sec_transactions_path):
                data['sec_transactions'] = pd.read_csv(sec_transactions_path)
            else:
                data['sec_transactions'] = self.sec_manager.get_sec_filings()

            
            if os.path.exists(insider_holdings_dir):
                # Load existing insider holdings data
                for insider_name in os.listdir(insider_holdings_dir):
                    insider_dir = os.path.join(insider_holdings_dir, insider_name)
                    if os.path.isdir(insider_dir):
                        holdings_file = os.path.join(insider_dir, 'holdings.csv')
                        if os.path.exists(holdings_file):
                            data['insider_holdings'][insider_name] = pd.read_csv(holdings_file)
            else:
                # Get new insider holdings data and save to files
                os.makedirs(insider_holdings_dir)
                data['insider_holdings'] = self.sec_manager.get_insider_holdings(data['sec_transactions'])
                
                for insider_name, holdings_df in data['insider_holdings'].items():
                    # Create directory for this insider
                    insider_dir = os.path.join(insider_holdings_dir, insider_name)
                    os.makedirs(insider_dir, exist_ok=True)
                    
                    # Save holdings to CSV
                    holdings_file = os.path.join(insider_dir, 'holdings.csv')
                    holdings_df.to_csv(holdings_file, index=False)

            if os.path.exists(insider_stocks_data_dir):
                data['insider_stocks_data'] = {}
                for ticker_file in os.listdir(insider_stocks_data_dir):
                    if ticker_file.endswith('.csv'):
                        ticker = ticker_file[:-4]  # Remove .csv extension
                        ticker_path = os.path.join(insider_stocks_data_dir, ticker_file)
                        data['insider_stocks_data'][ticker] = pd.read_csv(ticker_path)
            else:
                os.makedirs(insider_stocks_data_dir)
                unique_tickers = self.extractAllTickersFromInsiderHolding(data['insider_holdings'])
                data['insider_stocks_data'] = self.downloadAllInsiderHoldingStockTrends(unique_tickers.keys())
                
                for stock_ticker, stock_df in data['insider_stocks_data'].items():
                    # Save stock trend data to CSV with ticker name
                    stock_trend_file = os.path.join(insider_stocks_data_dir, f'{stock_ticker}.csv')
                    stock_df.to_csv(stock_trend_file, index=False)

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
                data['company_officers'] = pd.read_csv(company_officers_path)
            else:
                data['company_officers'] = self.sec_manager.get_board_members()

            if os.path.exists(company_description_path):
                with open(company_description_path, 'r') as f:
                    data['company_description'] = f.read()
            else:
                ticker_info = yf.Ticker(self.ticker).info
                data['company_description'] = ticker_info.get('longBusinessSummary', '')

            if os.path.exists(company_name_path):
                with open(company_name_path, 'r') as f:
                    data['company_name'] = f.read()
            else:
                ticker_info = yf.Ticker(self.ticker).info
                data['company_name'] = ticker_info.get('displayName', '')
           
            if os.path.exists(institutional_holders_path):
                data['institutional_holders'] = pd.read_csv(institutional_holders_path)
            else:
                data['institutional_holders'] = yf.Ticker(self.ticker).institutional_holders[['Holder', 'Shares']]

            if os.path.exists(competitors_path):
                with open(competitors_path, 'r') as f:
                    data['competitors'] = json.load(f)
            else:
                data['competitors'] = get_competitors(self.ticker)

            print("✅ Data successfully gathered for ticker " + self.ticker)
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
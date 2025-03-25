import os
import json
import pandas as pd
from typing import Dict, Any, Optional

class DataSaver:
    def __init__(self, base_directory: str = 'data'):
        self.base_directory = base_directory

    def save_data(self, data: Dict[str, Any], ticker: str) -> None:
        directory = os.path.join(self.base_directory, ticker)
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
                    stock_df.to_csv(stock_path, index=False)
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
                    print(f"[WARNING] Unsupported data type for key: {key}")

        print(f"[SUCCESS] Data successfully saved in {self.base_directory} for {ticker}")
        
    def load_saved_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Load previously saved data for a ticker"""
        try:
            directory = os.path.join(self.base_directory, ticker)
            if not os.path.exists(directory):
                print(f"[WARNING] No saved data found for {ticker} in {directory}")
                return None
                
            data = {}
            
            # Load simple files first (CSV, JSON, TXT)
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                if os.path.isfile(file_path):
                    key = os.path.splitext(file_name)[0]
                    ext = os.path.splitext(file_name)[1]
                    
                    if ext == '.csv':
                        data[key] = pd.read_csv(file_path)
                    elif ext == '.json':
                        with open(file_path, 'r') as f:
                            data[key] = json.load(f)
                    elif ext == '.txt':
                        with open(file_path, 'r') as f:
                            data[key] = f.read()
            
            # Load insider holdings (special structure)
            insider_holdings_dir = os.path.join(directory, 'insider_holdings')
            if os.path.exists(insider_holdings_dir):
                insider_holdings = {}
                for insider_name in os.listdir(insider_holdings_dir):
                    insider_dir = os.path.join(insider_holdings_dir, insider_name)
                    if os.path.isdir(insider_dir):
                        holdings_file = os.path.join(insider_dir, 'holdings.csv')
                        if os.path.exists(holdings_file):
                            insider_holdings[insider_name] = pd.read_csv(holdings_file)
                
                if insider_holdings:
                    data['insider_holdings'] = insider_holdings
            
            # Load insider stocks data (special structure)
            insider_stocks_dir = os.path.join(directory, 'insider_stocks_data')
            if os.path.exists(insider_stocks_dir):
                insider_stocks = {}
                for stock_file in os.listdir(insider_stocks_dir):
                    if stock_file.endswith('.csv'):
                        stock_ticker = os.path.splitext(stock_file)[0]
                        stock_path = os.path.join(insider_stocks_dir, stock_file)
                        insider_stocks[stock_ticker] = pd.read_csv(stock_path)
                
                if insider_stocks:
                    data['insider_stocks_data'] = insider_stocks
            
            return data
            
        except Exception as e:
            print(f"[ERROR] Failed to load saved data for {ticker}: {e}")
            return None 
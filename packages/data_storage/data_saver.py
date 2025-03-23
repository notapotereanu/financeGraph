import os
import json
import pandas as pd
from typing import Dict, Any

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

        print(f"✅ Data successfully saved in {self.base_directory}.") 
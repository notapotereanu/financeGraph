from typing import Optional
from packages.data_gathering.sec_data_manager import SECDataManager
from config import DEFAULT_STOCK_TICKER
from packages.data_gathering.data_gatherer import DataGatherer
from packages.data_storage.data_saver import DataSaver

class FinancialDataAnalyzer:
    def __init__(self, stock_tickers: Optional[list] = None):
        self.ticker = DEFAULT_STOCK_TICKER
        self.sec_manager = SECDataManager(self.ticker)
        self.data_gatherer = DataGatherer(self.ticker, self.sec_manager)
        self.data_saver = DataSaver()

    def run_analysis(self) -> None:
        try:
            all_data = self.data_gatherer.gather_data()
            self.data_saver.save_data(all_data, self.ticker)
            
        except Exception as e:
            print(f"❌ Error in analysis pipeline: {e}")
            raise 
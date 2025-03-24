from typing import Optional, Dict, Any, List
from packages.data_gathering.sec_data_manager import SECDataManager
from config import DEFAULT_STOCK_TICKER
from packages.data_gathering.data_gatherer import DataGatherer
from packages.data_storage.data_saver import DataSaver
from packages.data_storage.neo4j_manager import Neo4jManager

class FinancialDataAnalyzer:
    def __init__(self, stock_tickers: Optional[List[str]] = None):
        self.tickers = stock_tickers if stock_tickers else DEFAULT_STOCK_TICKER
        if isinstance(self.tickers, str):
            self.tickers = [self.tickers]
        self.data_saver = DataSaver()
        self.neo4j_manager = Neo4jManager()

    def run_analysis(self) -> None:
        try:
            # Removed the database clearing from here to prevent clearing on each run
            
            for ticker in self.tickers:
                print(f"[INFO] Starting analysis for {ticker}...")
                sec_manager = SECDataManager(ticker)
                data_gatherer = DataGatherer(ticker, sec_manager)
                
                # Gather data for current ticker
                all_data = data_gatherer.gather_data()
                self.data_saver.save_data(all_data, ticker)
                
                print(f"[SUCCESS] Analysis completed for all tickers: {', '.join(self.tickers)}")
            
        except Exception as e:
            print(f"[ERROR] Error in analysis pipeline: {e}")
            raise
            
    def save_to_neo4j(self, ticker: str = None, data: Dict[str, Any] = None) -> None:
        """Save gathered data to Neo4j graph database for a specific ticker."""
        try:
            # If no specific ticker is provided, save all gathered data
            if ticker is None and data is None:
                for ticker in self.tickers:
                    try:
                        print(f"[INFO] Saving data to Neo4j graph database for {ticker}...")
                        # Load data from saved files for this ticker
                        data_gatherer = DataGatherer(ticker)
                        data = data_gatherer.load_saved_data()
                        if data:
                            self.neo4j_manager.save_stock_data(ticker, data)
                            print(f"[SUCCESS] Data successfully saved to Neo4j graph database for {ticker}.")
                    except Exception as e:
                        print(f"[ERROR] Error saving data to Neo4j for {ticker}: {e}")
            # Save data for a specific ticker
            elif ticker and data:
                print(f"[INFO] Saving data to Neo4j graph database for {ticker}...")
                self.neo4j_manager.save_stock_data(ticker, data)
                print(f"[SUCCESS] Data successfully saved to Neo4j graph database for {ticker}.")
        except Exception as e:
            print(f"[ERROR] Error saving data to Neo4j: {e}")
        
    def close(self):
        """Close all connections."""
        self.neo4j_manager.close() 
"""Helper module for data analysis and SPARQL queries."""

import os
from typing import Dict, Any

from packages.data_gathering.tripleStoreStorage import TripleStoreStorage
from packages.data_analyser.queries import get_sparql_queries
from config import ONTOLOGY_PATH


class DataAnalyzer:
    """Handles data analysis and SPARQL queries."""
    
    def __init__(self, stock_ticker: str, storage: TripleStoreStorage):
        """
        Initialize the DataAnalyzer.
        
        Args:
            stock_ticker: The stock ticker symbol to analyze
            storage: TripleStoreStorage instance for RDF operations
        """
        self.stock_ticker = stock_ticker
        self.storage = storage
    
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
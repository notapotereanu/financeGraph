"""Fallback configuration file when the main config cannot be imported."""

from typing import List

# Default Settings
DEFAULT_STOCK_TICKER: List[str] = [
    "C", 
    "AAPL",
    "MSFT",
    "GOOGL"
]

# Neo4j connection parameters
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "financefinance"
NEO4J_DATABASE = "neo4j" 
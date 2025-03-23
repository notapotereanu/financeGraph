from typing import Dict, Any

# API Endpoints
TRIPLESTORE_ENDPOINT = "http://apotereanu:7200/repositories/test/statements"
SPARQL_QUERY_ENDPOINT = "http://apotereanu:7200/repositories/test"

# File Paths
ONTOLOGY_PATH = "rdf/finance.owl"

# API Keys and URLs
NEWS_API_KEY = "4f9a2b0c1efd40318cdf751d5b7444f1"
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"

# Default Settings
DEFAULT_STOCK_TICKER = "C"
DEFAULT_NEWS_ARTICLES = 100
DEFAULT_STOCK_HISTORY_DAYS = 180

# HTTP Headers
SEC_HEADERS: Dict[str, str] = {
    "User-Agent": "MyScraper/1.0 (https://www.mywebsite.com/contact; contact@mywebsite.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

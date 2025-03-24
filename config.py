from typing import Dict, List


# API Keys and URLs
NEWS_API_KEY = "4f9a2b0c1efd40318cdf751d5b7444f1"
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"
SEC_API_KEY = "822fa29be2ffa2c5e28113bfe4f2e800edc146b40cb8983dba499d31a7348ea5"


# Default Settings
DEFAULT_STOCK_TICKER: List[str] = ["IOT", "AAPL"]
DEFAULT_NEWS_ARTICLES = 100
DEFAULT_STOCK_HISTORY_DAYS = 180
SEC_FILES_TO_ANALYSE = 50

# HTTP Headers
SEC_HEADERS: Dict[str, str] = {
    "User-Agent": "MyScraper/1.0 (https://www.mywebsite.com/contact; contact@mywebsite.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

"""SPARQL queries for financial data analysis."""

from typing import Dict

def get_sparql_queries(stock_ticker: str) -> Dict[str, str]:
    """
    Get all SPARQL queries used in the application.
    
    Args:
        stock_ticker: The stock ticker symbol to use in queries
        
    Returns:
        Dictionary mapping query names to their SPARQL queries
    """
    return {
        "Stock Price Changes After SEC Filings": f"""
            PREFIX ex: <http://example.org/finance#>
            SELECT ?transactionDate ?stockPriceBefore ?stockPriceAfter
            WHERE {{
                ?transaction ex:date ?transactionDate .
                ?transaction ex:stockTicker "{stock_ticker}" .
                ?stockBefore ex:date ?transactionDate .
                ?stockBefore ex:close ?stockPriceBefore .
                ?stockAfter ex:date ?nextDate .
                ?stockAfter ex:close ?stockPriceAfter .
                FILTER (?nextDate > ?transactionDate)
            }}
            ORDER BY ?transactionDate
        """,
        
        "News Sentiment vs. Stock Price Movements": f"""
            PREFIX ex: <http://example.org/finance#>
            SELECT ?newsDate ?headline ?sentiment ?stockPriceBefore ?stockPriceAfter
            WHERE {{
                ?news ex:date ?newsDate .
                ?news ex:headline ?headline .
                ?news ex:sentiment ?sentiment .
                ?stockBefore ex:date ?newsDate .
                ?stockBefore ex:close ?stockPriceBefore .
                ?stockAfter ex:date ?nextDate .
                ?stockAfter ex:close ?stockPriceAfter .
                FILTER (?nextDate > ?newsDate)
            }}
            ORDER BY ?newsDate
        """,
        
        "Find Google Trends Impact on Stock Price": f"""
            PREFIX ex: <http://example.org/finance#>
            SELECT ?trendDate ?trendScore ?stockPriceBefore ?stockPriceAfter
            WHERE {{
                ?trend ex:date ?trendDate .
                ?trend ex:trendScore ?trendScore .
                ?stockBefore ex:date ?trendDate .
                ?stockBefore ex:close ?stockPriceBefore .
                ?stockAfter ex:date ?nextDate .
                ?stockAfter ex:close ?stockPriceAfter .
                FILTER (?nextDate > ?trendDate)
            }}
            ORDER BY ?trendDate
        """,
        
        "Compare Analyst Ratings vs. Real Stock Price": f"""
            PREFIX ex: <http://example.org/finance#>
            SELECT ?ratingDate ?analyst ?rating ?priceTarget ?stockPriceBefore ?stockPriceAfter
            WHERE {{
                ?rating ex:date ?ratingDate .
                ?rating ex:analyst ?analyst .
                ?rating ex:rating ?rating .
                ?rating ex:priceTarget ?priceTarget .
                ?stockBefore ex:date ?ratingDate .
                ?stockBefore ex:close ?stockPriceBefore .
                ?stockAfter ex:date ?nextDate .
                ?stockAfter ex:close ?stockPriceAfter .
                FILTER (?nextDate > ?ratingDate)
            }}
            ORDER BY ?ratingDate
        """,

        "Analyze Insider Holdings": f"""
            PREFIX ex: <http://example.org/finance#>
            SELECT ?insiderName ?stockTicker ?transactionDate ?transactionType ?shares ?value
            WHERE {{
                ?insider ex:name ?insiderName .
                ?insider ex:ownsStock ?stock .
                ?stock ex:stockTicker ?stockTicker .
                ?transaction ex:insiderName ?insiderName .
                ?transaction ex:stockTicker ?stockTicker .
                ?transaction ex:date ?transactionDate .
                ?transaction ex:transactionType ?transactionType .
                ?transaction ex:shares ?shares .
                ?transaction ex:value ?value .
            }}
            ORDER BY ?insiderName ?transactionDate
        """
    } 
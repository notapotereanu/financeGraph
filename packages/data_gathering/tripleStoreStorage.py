import requests
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Dict, Set

class TripleStoreStorage:
    """
    A class to handle storing RDF data and querying a triplestore.
    """

    def __init__(self, store_endpoint: str, query_endpoint: str):
        """
        Initialize with the endpoints for storing RDF and querying.
        
        :param store_endpoint: URL endpoint to post RDF data.
        :param query_endpoint: URL endpoint to execute SPARQL queries.
        """
        self.store_endpoint = store_endpoint
        self.query_endpoint = query_endpoint
        self.EX = Namespace("http://example.org/finance#")  # Define a better namespace

    def store(self, rdf_data: str) -> int:
        """
        Stores RDF data into the triplestore.
        
        :param rdf_data: RDF data in Turtle format.
        :return: HTTP status code from the POST request.
        """
        headers = {'Content-Type': 'text/turtle'}
        try:
            response = requests.post(self.store_endpoint, data=rdf_data, headers=headers)
            if response.status_code == 204:
                print("✅ RDF data successfully stored.")
            else:
                print(f"⚠️ Error storing RDF data. Status Code: {response.status_code}")
            return response.status_code
        except Exception as e:
            print(f"❌ Error storing RDF data: {e}")
            return None

    def query(self, query: str):
        """
        Executes a SPARQL query against the triplestore.
        
        :param query: A SPARQL query string.
        :return: The results of the query as a JSON object.
        """
        try:
            sparql = SPARQLWrapper(self.query_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            return sparql.query().convert()
        except Exception as e:
            print(f"❌ Error executing SPARQL query: {e}")
            return None

    def convert_sec_transactions_to_rdf(self, data: pd.DataFrame) -> str:
        """
        Converts SEC transactions data into RDF format.
        """
        g = Graph()
        for _, row in data.iterrows():
            transaction_uri = URIRef(self.EX["transaction_" + str(row['date'])])

            g.add((transaction_uri, RDF.type, self.EX.StockTransaction))
            g.add((transaction_uri, self.EX.date, Literal(row['date'], datatype=XSD.date)))
            g.add((transaction_uri, self.EX.stockTicker, Literal(row['stock_ticker'], datatype=XSD.string)))
            g.add((transaction_uri, self.EX.price, Literal(row['price'], datatype=XSD.decimal)))
            g.add((transaction_uri, self.EX.insiderName, Literal(row['insider_name'], datatype=XSD.string)))
            g.add((transaction_uri, self.EX.transactionType, Literal(row['transaction_type'], datatype=XSD.string)))
            g.add((transaction_uri, self.EX.shares, Literal(row['shares'], datatype=XSD.integer)))
            g.add((transaction_uri, self.EX.value, Literal(row['value'], datatype=XSD.decimal)))
        
        return g.serialize(format='turtle')

    def convert_google_trends_to_rdf(self, data: pd.DataFrame) -> str:
        """
        Converts Google Trends data into RDF format.
        """
        g = Graph()
        for _, row in data.iterrows():
            trend_uri = URIRef(self.EX["trend_" + str(row['date'])])

            g.add((trend_uri, RDF.type, self.EX.GoogleTrend))
            g.add((trend_uri, self.EX.date, Literal(row['date'], datatype=XSD.date)))
            g.add((trend_uri, self.EX.trendScore, Literal(row['trend_score'], datatype=XSD.integer)))
        
        return g.serialize(format='turtle')

    def convert_news_sentiment_to_rdf(self, data: pd.DataFrame) -> str:
        """
        Converts News Sentiment data into RDF format.
        """
        g = Graph()
        for _, row in data.iterrows():
            news_uri = URIRef(self.EX["news_" + str(row['date'])])

            g.add((news_uri, RDF.type, self.EX.NewsSentiment))
            g.add((news_uri, self.EX.date, Literal(row['date'], datatype=XSD.date)))
            g.add((news_uri, self.EX.source, Literal(row['source'], datatype=XSD.string)))
            g.add((news_uri, self.EX.headline, Literal(row['headline'], datatype=XSD.string)))
            g.add((news_uri, self.EX.sentiment, Literal(row['sentiment_score'], datatype=XSD.decimal)))
        
        return g.serialize(format='turtle')

    def convert_stock_data_to_rdf(self, data: pd.DataFrame) -> str:
        """
        Converts Stock Data (Yahoo Finance) into RDF format.
        """
        g = Graph()
        for index, row in data.iterrows():
            stock_uri = URIRef(self.EX["stock_" + str(index)])

            g.add((stock_uri, RDF.type, self.EX.StockPrice))
            g.add((stock_uri, self.EX.date, Literal(row['Date'], datatype=XSD.date)))
            g.add((stock_uri, self.EX.open, Literal(row['Open'], datatype=XSD.decimal)))
            g.add((stock_uri, self.EX.close, Literal(row['Close'], datatype=XSD.decimal)))
            g.add((stock_uri, self.EX.high, Literal(row['High'], datatype=XSD.decimal)))
            g.add((stock_uri, self.EX.low, Literal(row['Low'], datatype=XSD.decimal)))
            g.add((stock_uri, self.EX.volume, Literal(row['Volume'], datatype=XSD.integer)))
        
        return g.serialize(format='turtle')

    def convert_analysts_ratings_to_rdf(self, data: pd.DataFrame) -> str:
        """
        Converts Analysts Ratings into RDF format.
        """
        g = Graph()
        for _, row in data.iterrows():
            rating_uri = URIRef(self.EX["rating_" + str(row['date'])])

            g.add((rating_uri, RDF.type, self.EX.AnalystRating))
            g.add((rating_uri, self.EX.date, Literal(row['date'], datatype=XSD.date)))
            g.add((rating_uri, self.EX.analyst, Literal(row['analyst'], datatype=XSD.string)))
            g.add((rating_uri, self.EX.rating, Literal(row['rating'], datatype=XSD.string)))
            g.add((rating_uri, self.EX.priceTarget, Literal(row['price_target'], datatype=XSD.decimal)))
        
        return g.serialize(format='turtle')
    
    def load_ontology(self, ontology_path: str):
        """
        Loads an OWL ontology into the triplestore.
        
        :param ontology_path: Path to the ontology file.
        """
        try:
            with open(ontology_path, "r", encoding="utf-8") as file:
                ontology_data = file.read()

            headers = {'Content-Type': 'text/turtle'}
            response = requests.post(self.store_endpoint, data=ontology_data, headers=headers)

            if response.status_code == 204:
                print("✅ Ontology successfully uploaded to the triplestore.")
            else:
                print(f"⚠️ Error uploading ontology. Status Code: {response.status_code}")
        except Exception as e:
            print(f"❌ Error loading ontology: {e}")
            
    def query_dbpedia(self, query: str):
        """
        Executes a SPARQL query against the DBpedia endpoint.
        
        :param query: A SPARQL query string.
        :return: The results of the query as a JSON object.
        """
        DBPEDIA_SPARQL_ENDPOINT = "http://dbpedia.org/sparql"
        
        try:
            sparql = SPARQLWrapper(DBPEDIA_SPARQL_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            return results
        except Exception as e:
            print(f"❌ Error executing DBpedia query: {e}")
            return None

    def convert_insider_holdings_to_rdf(self, insider_holdings: Dict[str, Set[str]]) -> str:
        """
        Converts insider holdings data into RDF format.
        
        Args:
            insider_holdings: Dictionary mapping insider names to sets of stock tickers they own
            
        Returns:
            RDF data in Turtle format
        """
        g = Graph()
        
        for insider_name, holdings in insider_holdings.items():
            # Create a URI for the insider
            insider_uri = URIRef(self.EX[f"insider_{insider_name.replace(' ', '_')}"])
            
            # Add the insider as an instance of Insider class
            g.add((insider_uri, RDF.type, self.EX.Insider))
            g.add((insider_uri, self.EX.name, Literal(insider_name, datatype=XSD.string)))
            
            # Add each stock holding
            for stock_ticker in holdings:
                stock_uri = URIRef(self.EX[f"stock_{stock_ticker}"])
                g.add((insider_uri, self.EX.ownsStock, stock_uri))
        
        return g.serialize(format='turtle')


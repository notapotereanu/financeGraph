import pandas as pd
import numpy as np
from neo4j import GraphDatabase
from typing import Dict, Any
import logging
import time
import os

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("neo4j_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Neo4jManager")

class Neo4jManager:
    """Handles saving financial data to a Neo4j graph database."""
    
    def __init__(self, uri="bolt://localhost:7687", username="neo4j", password="financefinance", database="neo4j"):
        """
        Initialize the Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        logger.info(f"Initializing Neo4jManager with URI: {uri}, database: {database}")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.database = database
            # Test connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_result = result.single()
                if test_result and test_result["test"] == 1:
                    logger.info("Successfully connected to Neo4j database")
                else:
                    logger.warning("Connection established but test query returned unexpected result")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {e}")
            raise
        
    def close(self):
        """Close the Neo4j connection."""
        logger.info("Closing Neo4j connection")
        try:
            self.driver.close()
            logger.info("Neo4j connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {e}")
        
    def clear_database(self):
        """Clear all nodes and relationships in the database."""
        logger.info(f"Clearing all data from Neo4j database: {self.database}")
        start_time = time.time()
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = result.single()["count"]
                logger.info(f"Found {node_count} nodes to delete")
                
                session.run("MATCH (n) DETACH DELETE n")
                
                result = session.run("MATCH (n) RETURN count(n) as count")
                remaining = result.single()["count"]
                logger.info(f"Database cleared. Remaining nodes: {remaining}")
                
            elapsed = time.time() - start_time
            logger.info(f"Database cleared in {elapsed:.2f} seconds")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            raise
            
    def _sanitize_value(self, value):
        """
        Convert values to formats suitable for Neo4j.
        
        Args:
            value: The value to sanitize
            
        Returns:
            The sanitized value
        """
        try:
            if isinstance(value, pd.DataFrame):
                logger.debug(f"Sanitizing DataFrame with shape {value.shape}")
                return value.to_dict(orient='records')
            elif isinstance(value, pd.Series):
                logger.debug(f"Sanitizing Series with length {len(value)}")
                return value.to_dict()
            elif isinstance(value, (np.integer, np.floating)):
                logger.debug("Sanitizing numpy numeric type")
                return float(value)
            elif pd.isna(value):
                logger.debug("Sanitizing NaN value to None")
                return None
            elif isinstance(value, (dict, list)):
                logger.debug(f"Passing through dict/list with type {type(value)}")
                return value
            else:
                logger.debug(f"Converting {type(value)} to string")
                return str(value)
        except Exception as e:
            logger.error(f"Error sanitizing value of type {type(value)}: {e}")
            # Fallback to string if possible
            try:
                return str(value)
            except:
                logger.error("Failed to sanitize value, returning None")
                return None
            
    def save_stock_data(self, ticker, data):
        """
        Save all stock data to Neo4j.
        
        Args:
            ticker: The stock ticker symbol
            data: Dictionary containing all the stock data
        """
        logger.info(f"Starting to save data for ticker: {ticker}")
        start_time = time.time()
        
        try:
            with self.driver.session(database=self.database) as session:
                # Create Stock node with all data
                logger.info(f"Creating main Stock node for {ticker}")
                session.run(
                    """
                    MERGE (s:Stock {ticker: $ticker})
                    SET s.name = $company_name,
                        s.description = $description,
                        s.price_data_file = $price_file
                    """,
                    ticker=ticker,
                    company_name=data.get('company_name', ticker),
                    description=data.get('company_description', ''),
                    price_file=f"data/{ticker}/stock_prices.csv"
                )
                logger.info(f"Main Stock node created/updated for {ticker}")
                
                # Save stock data to CSV if it exists
                stock_data = data.get('stock_data')
                if stock_data is not None and not stock_data.empty:
                    logger.info(f"Saving stock price data to CSV for {ticker}")
                    csv_path = f"data/{ticker}/stock_prices.csv"
                    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                    stock_data.to_csv(csv_path)
                    logger.info(f"Saved {len(stock_data)} price records to {csv_path}")
                else:
                    logger.warning(f"No stock price data available for {ticker}")
                
                # Process different data categories
                categories = [
                    ('insider_holdings', 'Insider Holdings'),
                    ('sec_transactions', 'SEC Transactions'),
                    ('company_officers', 'Company Officers'),
                    ('institutional_holders', 'Institutional Holders'),
                    ('competitors', 'Competitors'),
                    ('analysts_ratings', 'Analyst Ratings'),
                    ('news_sentiment', 'News Sentiment')
                ]
                
                for key, label in categories:
                    logger.info(f"Processing {label} for {ticker}")
                    category_start = time.time()
                    
                    try:
                        category_data = data.get(key, {} if key == 'insider_holdings' else None)
                        if category_data is not None and (not isinstance(category_data, pd.DataFrame) or not category_data.empty):
                            method = getattr(self, f"_save_{key}")
                            method(session, ticker, category_data)
                            logger.info(f"Completed saving {label} for {ticker}")
                        else:
                            logger.warning(f"No {label} data available for {ticker}")
                    except Exception as e:
                        logger.error(f"Error processing {label} for {ticker}: {e}")
                    
                    logger.info(f"Completed {label} in {time.time() - category_start:.2f} seconds")
            
            total_time = time.time() - start_time
            logger.info(f"Completed saving all data for {ticker} in {total_time:.2f} seconds")
        
        except Exception as e:
            logger.error(f"Failed to save data for {ticker}: {e}")
            raise
            
    def _save_company_description(self, session, ticker, data):
        session.run(
                """
                MATCH (s:Stock {ticker: $ticker})
                MERGE (d:Description {text: $description})
                MERGE (s)-[:HAS_DESCRIPTION]->(d)
                """,
                ticker=ticker,
                description=data
            )
        
    def _save_stock_price_data(self, session, ticker, stock_data):
        """
        Save stock price data to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            stock_data: DataFrame containing stock price data
        """
        if stock_data is None or stock_data.empty:
            return
            
        # Save reference to data file location
        file_path = f"data/{ticker}/stock_prices.csv"
        
        # Save stock data to CSV file
        stock_data.to_csv(file_path)
            
        # Create StockTrend node with file path
        session.run(
            """
            MATCH (s:Stock {ticker: $ticker})
            MERGE (t:StockTrend {stock: $ticker})
            SET t.data_file = $file_path
            MERGE (s)-[:HAS_TREND]->(t)
            """,
            ticker=ticker,
            file_path=file_path
        )
    
    def _save_insider_holdings(self, session, ticker, insider_holdings):
        """
        Save insider holdings data to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            insider_holdings: Dictionary of insider holdings
        """
        logger.info(f"Saving insider holdings for {ticker}")
        
        if not insider_holdings:
            logger.warning(f"No insider holdings data available for {ticker}")
            return
        
        try:
            # Create InsiderTraders node and connect to stock
            logger.info(f"Creating InsiderTraders node for {ticker}")
            insider_node_name = f"Insider Trading - {ticker}"
            session.run(
                """
                MATCH (s:Stock {ticker: $ticker})
                MERGE (it:InsiderTraders {name: $insider_name})
                MERGE (it)-[:ASSOCIATED_WITH]->(s)
                """,
                ticker=ticker,
                insider_name=insider_node_name
            )
            logger.info(f"InsiderTraders node created: {insider_node_name}")
            
            # Store file paths for insiders' holdings
            insider_holdings_path = f"data/{ticker}/insider_holdings"
            logger.info(f"Processing {len(insider_holdings)} insider records")
            
            for insider_name, holdings_df in insider_holdings.items():
                if holdings_df.empty:
                    logger.debug(f"Empty holdings for insider: {insider_name}, skipping")
                    continue
                
                logger.info(f"Processing insider: {insider_name} with {len(holdings_df)} holdings records")
                
                # Get the first row to extract total shares and relationship
                first_row = holdings_df.iloc[0]
                shares_total = float(first_row.get('shares_total', 0)) if not pd.isna(first_row.get('shares_total')) else 0
                relationship = first_row.get('relationship', '')
                
                # CSV path for this insider's holdings
                insider_csv_path = f"{insider_holdings_path}/{insider_name}/holdings.csv"
                
                # Create Insider node with properties and connect to InsiderTraders
                logger.debug(f"Creating Insider node for {insider_name}")
                session.run(
                    """
                    MATCH (it:InsiderTraders {name: $insider_name})-[:ASSOCIATED_WITH]->(s:Stock {ticker: $ticker})
                    MERGE (i:Insider {name: $name, ticker: $ticker})
                    SET i.shares_total = $shares_total,
                        i.relationship = $relationship,
                        i.holdings_file = $holdings_file
                    MERGE (i)-[:BELONGS_TO]->(it)
                    """,
                    ticker=ticker,
                    insider_name=insider_node_name,
                    name=insider_name,
                    shares_total=shares_total,
                    relationship=relationship,
                    holdings_file=insider_csv_path
                )
                logger.debug(f"Created Insider node for {insider_name} with {shares_total} shares")
                
                # For each security held (excluding the main ticker)
                # Group by issuerTradingSymbol and get the most recent row by date for each stock
                securities = holdings_df.groupby('issuerTradingSymbol')
                logger.info(f"Processing {len(securities)} securities held by {insider_name}")
                
                for symbol, group_df in securities:
                    if pd.isna(symbol) or symbol == ticker:
                        logger.debug(f"Skipping {symbol} (same as main ticker or NaN)")
                        continue
                    
                    # CSV path for this stock's data
                    stock_csv_path = f"data/{ticker}/insider_stocks_data/{symbol}.csv"
                    
                    # Try to sort by date to get the most recent record
                    try:
                        logger.debug(f"Processing holdings for security: {symbol}")
                        if 'date' in group_df.columns:
                            # Sort by date in descending order
                            group_df = group_df.sort_values('date', ascending=False)
                            logger.debug(f"Sorted {len(group_df)} records by date")
                        
                        # Get the most recent row
                        latest_row = group_df.iloc[0]
                        
                        # Extract stock name if available (fallback to symbol if not)
                        stock_name = latest_row.get('issuerName', symbol)
                        
                        # Get shares and relationship from the latest row
                        shares = float(latest_row.get('shares_total', 0)) if not pd.isna(latest_row.get('shares_total')) else 0
                        relationship = latest_row.get('relationship', '')
                        transaction_date = latest_row.get('date', '')
                        
                        # Format date if it's a datetime
                        if hasattr(transaction_date, 'strftime'):
                            date_str = transaction_date.strftime('%Y-%m-%d')
                        else:
                            date_str = str(transaction_date)
                        
                        logger.debug(f"Creating Stock node for {symbol} and relationship from {insider_name}")
                        # Create Security node and relationships with the stock name and CSV path
                        session.run(
                            """
                            MATCH (i:Insider {name: $insider_name, ticker: $ticker})
                            MERGE (s:Stock {ticker: $symbol})
                            SET s.name = $stock_name,
                                s.data_file = $data_file
                            MERGE (i)-[h:HOLDS]->(s)
                            SET h.shares = $shares,
                                h.relationship = $relationship,
                                h.last_updated = $date
                            """,
                            insider_name=insider_name,
                            ticker=ticker,
                            symbol=symbol,
                            stock_name=stock_name,
                            data_file=stock_csv_path,
                            shares=shares,
                            relationship=relationship,
                            date=date_str
                        )
                        logger.debug(f"Created stock node and relationship for {symbol} with {shares} shares")
                    except Exception as e:
                        logger.error(f"Error processing insider holdings for {symbol}: {e}")
                        logger.info("Trying fallback approach")
                        # Fallback to the basic approach if there was an error
                        try:
                            session.run(
                                """
                                MATCH (i:Insider {name: $insider_name, ticker: $ticker})
                                MERGE (s:Stock {ticker: $symbol})
                                SET s.data_file = $data_file
                                MERGE (i)-[h:HOLDS]->(s)
                                SET h.shares = $shares,
                                    h.relationship = $relationship
                                """,
                                insider_name=insider_name,
                                ticker=ticker,
                                symbol=symbol,
                                data_file=stock_csv_path,
                                shares=float(group_df.iloc[0].get('shares_total', 0)) if not pd.isna(group_df.iloc[0].get('shares_total')) else 0,
                                relationship=group_df.iloc[0].get('relationship', '')
                            )
                            logger.info(f"Successfully created relationship using fallback approach for {symbol}")
                        except Exception as sub_e:
                            logger.error(f"Fallback approach also failed for {symbol}: {sub_e}")
            
            logger.info(f"Successfully completed saving insider holdings for {ticker}")
        except Exception as e:
            logger.error(f"Failed to save insider holdings for {ticker}: {e}")
            raise
    
    def _save_sec_transactions(self, session, ticker, sec_transactions):
        """
        Save SEC transactions to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            sec_transactions: DataFrame of SEC transactions
        """
        logger.info(f"Saving SEC transactions for {ticker}")
        
        if sec_transactions is None or sec_transactions.empty:
            logger.warning(f"No SEC transactions available for {ticker}")
            return
        
        logger.info(f"Processing {len(sec_transactions)} SEC transactions")
        transaction_count = 0
        skipped_count = 0
        
        try:
            for idx, row in sec_transactions.iterrows():
                insider_name = row.get('insider_name')
                transaction_date = row.get('date')
                
                if pd.isna(insider_name) or pd.isna(transaction_date):
                    logger.debug(f"Skipping transaction at index {idx} due to missing insider name or date")
                    skipped_count += 1
                    continue
                
                try:
                    # Convert date to string format if it's a datetime
                    if hasattr(transaction_date, 'strftime'):
                        date_str = transaction_date.strftime('%Y-%m-%d')
                    else:
                        date_str = str(transaction_date)
                    
                    symbol = row.get('issuerTradingSymbol', ticker)
                    shares = float(row.get('shares', 0)) if not pd.isna(row.get('shares')) else 0
                    price = float(row.get('price', 0)) if not pd.isna(row.get('price')) else 0
                    value = float(row.get('value', 0)) if not pd.isna(row.get('value')) else 0
                    
                    logger.debug(f"Creating Transaction node for {insider_name} on {date_str} for {symbol}")
                    # Create Transaction node
                    session.run(
                        """
                        MATCH (i:Insider {name: $insider_name, ticker: $ticker})
                        MERGE (t:Transaction {
                            date: $date,
                            insider: $insider_name,
                            stock: $symbol,
                            ticker: $ticker
                        })
                        SET t.type = $type,
                            t.shares = $shares,
                            t.price = $price,
                            t.value = $value
                        MERGE (i)-[:MADE]->(t)
                        """,
                        ticker=ticker,
                        insider_name=insider_name,
                        symbol=symbol,
                        date=date_str,
                        type=row.get('transaction_type', ''),
                        shares=shares,
                        price=price,
                        value=value
                    )
                    transaction_count += 1
                    logger.debug(f"Created Transaction node for {shares} shares at ${price} (value: ${value})")
                except Exception as e:
                    logger.error(f"Error creating SEC transaction for {insider_name} on {transaction_date}: {e}")
            
            logger.info(f"Completed saving SEC transactions: {transaction_count} created, {skipped_count} skipped")
        except Exception as e:
            logger.error(f"Failed to save SEC transactions for {ticker}: {e}")
            raise
    
    def _save_company_officers(self, session, ticker, company_officers):
        """
        Save company officers to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            company_officers: DataFrame or dictionary of company officers
        """
        if company_officers is None or (isinstance(company_officers, pd.DataFrame) and company_officers.empty):
            return
            
        # Create CompanyOfficers node and connect to stock
        session.run(
            """
            MATCH (s:Stock {ticker: $ticker})
            MERGE (co:CompanyOfficers {name: $officers_name})
            MERGE (co)-[:ASSOCIATED_WITH]->(s)
            """,
            ticker=ticker,
            officers_name=f"Company Officers - {ticker}"
        )
        
        # Store file path for company officers data
        officers_file_path = f"data/{ticker}/company_officers.csv"
        
        try:
            # Add file path to the CompanyOfficers node
            session.run(
                """
                MATCH (co:CompanyOfficers {name: $officers_name})-[:ASSOCIATED_WITH]->(s:Stock {ticker: $ticker})
                SET co.data_file = $data_file
                """,
                ticker=ticker,
                officers_name=f"Company Officers - {ticker}",
                data_file=officers_file_path
            )
            
            # Process each officer
            for _, row in company_officers.iterrows():
                name = row.get('name')
                if pd.isna(name):
                    continue
                
                position = row.get('position', '')
                age = int(row.get('age', 0)) if not pd.isna(row.get('age')) else 0
                
                # Create Officer node and connect to CompanyOfficers
                session.run(
                    """
                    MATCH (co:CompanyOfficers {name: $officers_name})-[:ASSOCIATED_WITH]->(s:Stock {ticker: $ticker})
                    MERGE (o:Officer {name: $name, ticker: $ticker})
                    SET o.position = $position,
                        o.age = $age
                    MERGE (o)-[:BELONGS_TO]->(co)
                    """,
                    ticker=ticker,
                    officers_name=f"Company Officers - {ticker}",
                    name=name,
                    position=position,
                    age=age
                )
        except Exception as e:
            print(f"Error saving company officers: {e}")
            # Fallback approach - connect directly to stock
            try:
                for _, row in company_officers.iterrows():
                    name = row.get('name')
                    if pd.isna(name):
                        continue
                        
                    # Create Officer node with direct connection to stock
                    session.run(
                        """
                        MATCH (s:Stock {ticker: $ticker})
                        MERGE (o:Officer {name: $name, ticker: $ticker})
                        SET o.position = $position,
                            o.age = $age
                        MERGE (o)-[:WORKS_FOR]->(s)
                        """,
                        ticker=ticker,
                        name=name,
                        position=row.get('position', ''),
                        age=int(row.get('age', 0)) if not pd.isna(row.get('age')) else 0
                    )
            except Exception as e:
                print(f"Fallback for company officers also failed: {e}")
    
    def _save_institutional_holders(self, session, ticker, institutional_holders):
        """
        Save institutional holders to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            institutional_holders: DataFrame of institutional holders, which should include a 'Ticker' column
                                  for the institution's own ticker symbol
        """
        logger.info(f"Saving institutional holders for {ticker}")
        
        if institutional_holders is None or institutional_holders.empty:
            logger.warning(f"No institutional holders data available for {ticker}")
            return
        
        holders_node_name = f"Institutional Holders - {ticker}"
        # Store file path for institutional holders data
        institutional_file_path = f"data/{ticker}/institutional_holders.csv"
        
        try:
            # Create InstitutionalHolders node and connect to stock
            logger.info(f"Creating InstitutionalHolders node for {ticker}")
            session.run(
                """
                MATCH (s:Stock {ticker: $ticker})
                MERGE (ih:InstitutionalHolders {name: $holders_name})
                MERGE (ih)-[:ASSOCIATED_WITH]->(s)
                """,
                ticker=ticker,
                holders_name=holders_node_name
            )
            logger.info(f"InstitutionalHolders node created: {holders_node_name}")
            
            # Add file path to the InstitutionalHolders node
            logger.debug(f"Setting data file path: {institutional_file_path}")
            session.run(
                """
                MATCH (ih:InstitutionalHolders {name: $holders_name})-[:ASSOCIATED_WITH]->(s:Stock {ticker: $ticker})
                SET ih.data_file = $data_file
                """,
                ticker=ticker,
                holders_name=holders_node_name,
                data_file=institutional_file_path
            )
            
            # Process each institutional holder
            logger.info(f"Processing {len(institutional_holders)} institutional holders")
            institution_count = 0
            skipped_count = 0
            
            for idx, row in institutional_holders.iterrows():
                holder = row.get('Holder')
                if pd.isna(holder):
                    logger.debug(f"Skipping holder at index {idx} due to missing holder name")
                    skipped_count += 1
                    continue
                
                try:
                    shares = float(row.get('Shares', 0)) if not pd.isna(row.get('Shares')) else 0
                    
                    # Get institution ticker if available in the DataFrame
                    institution_ticker = row.get('Ticker', '')
                    if pd.isna(institution_ticker):
                        institution_ticker = ''
                        logger.debug(f"No ticker available for institution: {holder}")
                    else:
                        logger.debug(f"Found ticker {institution_ticker} for institution: {holder}")
                    
                    # Create Stock node for the institution and connect to InstitutionalHolders with shares in the relationship
                    logger.debug(f"Creating Stock node for institution: {holder} with ticker: {institution_ticker}")
                    session.run(
                        """
                        MATCH (ih:InstitutionalHolders {name: $holders_name})-[:ASSOCIATED_WITH]->(s:Stock {ticker: $ticker})
                        MERGE (i:Stock {ticker: $institution_ticker})
                        SET i.name = $name
                        MERGE (i)-[r:BELONGS_TO]->(ih)
                        SET r.shares = $shares
                        """,
                        ticker=ticker,
                        holders_name=holders_node_name,
                        name=holder,
                        institution_ticker=institution_ticker,
                        shares=shares
                    )
                    institution_count += 1
                    logger.debug(f"Created institution node for {holder} with {shares} shares")
                except Exception as e:
                    logger.error(f"Error creating institution node for {holder}: {e}")
            
            logger.info(f"Completed saving institutional holders: {institution_count} created, {skipped_count} skipped")
                
        except Exception as e:
            logger.error(f"Error saving institutional holders: {e}")
            logger.info("Trying fallback approach - direct connections")
            
            try:
                logger.info(f"Processing {len(institutional_holders)} institutional holders using fallback approach")
                fallback_count = 0
                
                for idx, row in institutional_holders.iterrows():
                    holder = row.get('Holder')
                    if pd.isna(holder):
                        continue
                    
                    try:
                        shares = float(row.get('Shares', 0)) if not pd.isna(row.get('Shares')) else 0
                        
                        # Get institution ticker if available
                        institution_ticker = row.get('Ticker', '')
                        if pd.isna(institution_ticker):
                            institution_ticker = ''
                        
                        # Create Stock node for the institution with direct connection to the company stock
                        logger.debug(f"Creating Stock node with direct connection for {holder}")
                        session.run(
                            """
                            MATCH (s:Stock {ticker: $ticker})
                            MERGE (i:Stock {ticker: $institution_ticker})
                            SET i.name = $name
                            MERGE (i)-[h:HOLDS]->(s)
                            SET h.shares = $shares
                            """,
                            ticker=ticker,
                            name=holder,
                            institution_ticker=institution_ticker,
                            shares=shares
                        )
                        fallback_count += 1
                        logger.debug(f"Created direct relationship for {holder} with {shares} shares")
                    except Exception as sub_e:
                        logger.error(f"Error in fallback for institution {holder}: {sub_e}")
                
                logger.info(f"Completed fallback approach: {fallback_count} direct relationships created")
            except Exception as fallback_e:
                logger.error(f"Fallback for institutional holders also failed: {fallback_e}")
    
    def _save_competitors(self, session, ticker, competitors):
        """
        Save competitors to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            competitors: Array of dictionaries, each containing 'ticker' and 'name' of a competitor
        """
        if not competitors:
            return
        
        # Create Competitors node and connect to stock
        session.run(
            """
            MATCH (s:Stock {ticker: $ticker})
            MERGE (c:Competitors {name: $competitors_name})
            MERGE (c)-[:COMPEETES_WITH]->(s)
            """,
            ticker=ticker,
            competitors_name=f"Competitors - {ticker}"
        )
        
        # Store file path for competitors data
        competitors_file_path = f"data/{ticker}/competitors.json"
        
        try:
            # Add file path to the Competitors node
            session.run(
                """
                MATCH (c:Competitors {name: $competitors_name})-[:COMPEETES_WITH]->(s:Stock {ticker: $ticker})
                SET c.data_file = $data_file
                """,
                ticker=ticker,
                competitors_name=f"Competitors - {ticker}",
                data_file=competitors_file_path
            )
            
            # Process each competitor
            for competitor in competitors:
                # Extract ticker and name from competitor dictionary
                if isinstance(competitor, dict):
                    # Check if it has 'ticker' key (preferred) or fallback to 'symbol'
                    if 'ticker' in competitor:
                        comp_ticker = competitor.get('ticker')
                    elif 'symbol' in competitor:
                        comp_ticker = competitor.get('symbol')
                    else:
                        # Skip if no ticker/symbol
                        continue
                        
                    comp_name = competitor.get('name', comp_ticker)
                else:
                    # Handle case where competitor might be a string
                    comp_ticker = str(competitor)
                    comp_name = str(competitor)
                
                if not comp_ticker:
                    continue
                
                # Create Competitor Stock node and connect to Competitors node
                session.run(
                    """
                    MATCH (c:Competitors {name: $competitors_name})-[:COMPEETES_WITH]->(s:Stock {ticker: $ticker})
                    MERGE (cs:Stock {ticker: $comp_ticker})
                    SET cs.name = $comp_name
                    MERGE (cs)-[:BELONGS_TO]->(c)
                    """,
                    ticker=ticker,
                    competitors_name=f"Competitors - {ticker}",
                    comp_ticker=comp_ticker,
                    comp_name=comp_name
                )
                
        except Exception as e:
            print(f"Error saving competitors: {e}")
            # Fallback approach - direct relationships
            try:
                for competitor in competitors:
                    # Extract ticker and name from competitor dictionary
                    if isinstance(competitor, dict):
                        # Check if it has 'ticker' key (preferred) or fallback to 'symbol'
                        if 'ticker' in competitor:
                            comp_ticker = competitor.get('ticker')
                        elif 'symbol' in competitor:
                            comp_ticker = competitor.get('symbol')
                        else:
                            # Skip if no ticker/symbol
                            continue
                            
                        comp_name = competitor.get('name', comp_ticker)
                    else:
                        # Handle case where competitor might be a string
                        comp_ticker = str(competitor)
                        comp_name = str(competitor)
                    
                    if not comp_ticker:
                        continue
                    
                    # Direct competitor relationships
                    session.run(
                        """
                        MATCH (s:Stock {ticker: $ticker})
                        MERGE (c:Stock {ticker: $comp_ticker})
                        SET c.name = $comp_name
                        MERGE (s)-[:COMPETES_WITH]->(c)
                        MERGE (c)-[:COMPETES_WITH]->(s)
                        """,
                        ticker=ticker,
                        comp_ticker=comp_ticker,
                        comp_name=comp_name
                    )
            except Exception as e:
                print(f"Fallback for competitors also failed: {e}")
    
    def _save_analyst_ratings(self, session, ticker, analysts_ratings):
        """
        Save analyst ratings to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            analysts_ratings: DataFrame of analyst ratings with columns:
                Date, Action, Analyst, Rating Change, Price Target Change
        """
        logger.info(f"Saving analyst ratings for {ticker}")
        
        if analysts_ratings is None or analysts_ratings.empty:
            logger.warning(f"No analyst ratings available for {ticker}")
            return
            
        analysis_node_name = f"Analyst Ratings - {ticker}"
        # Store file path for analyst ratings data
        ratings_file_path = f"data/{ticker}/analysts_ratings.csv"
        
        try:
            # Create Analysis node and connect to stock
            logger.info(f"Creating Analysis node for {ticker}")
            session.run(
                """
                MATCH (s:Stock {ticker: $ticker})
                MERGE (a:Analysis {name: $analysis_name})
                MERGE (a)-[:RATES]->(s)
                """,
                ticker=ticker,
                analysis_name=analysis_node_name
            )
            logger.info(f"Analysis node created: {analysis_node_name}")
            
            # Add file path to the Analysis node
            logger.debug(f"Setting data file path: {ratings_file_path}")
            session.run(
                """
                MATCH (a:Analysis {name: $analysis_name})-[:RATES]->(s:Stock {ticker: $ticker})
                SET a.data_file = $data_file
                """,
                ticker=ticker,
                analysis_name=analysis_node_name,
                data_file=ratings_file_path
            )
            
            # Group by Analyst to get the most recent rating from each analyst
            if 'Analyst' in analysts_ratings.columns and 'Date' in analysts_ratings.columns:
                logger.info(f"Processing analyst ratings with grouping by analyst")
                
                # Convert Date to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(analysts_ratings['Date']):
                    try:
                        logger.debug("Converting Date column to datetime")
                        analysts_ratings['Date'] = pd.to_datetime(analysts_ratings['Date'])
                        logger.debug("Date conversion successful")
                    except Exception as e:
                        logger.warning(f"Failed to convert dates to datetime: {e}")
                
                # Sort by Date in descending order
                logger.debug("Sorting ratings by date in descending order")
                analysts_ratings = analysts_ratings.sort_values('Date', ascending=False)
                
                # Get most recent rating from each analyst
                logger.debug("Getting most recent rating for each analyst")
                latest_ratings = analysts_ratings.drop_duplicates(subset=['Analyst'])
                logger.info(f"Found {len(latest_ratings)} unique analysts with ratings")
                
                analyst_count = 0
                skipped_count = 0
                
                # Process each analyst's latest rating
                for idx, row in latest_ratings.iterrows():
                    analyst = row.get('Analyst')
                    date = row.get('Date')
                    
                    if pd.isna(analyst) or pd.isna(date):
                        logger.debug(f"Skipping analyst at index {idx} due to missing analyst name or date")
                        skipped_count += 1
                        continue
                    
                    try:
                        # Convert date to string format if it's a datetime
                        if hasattr(date, 'strftime'):
                            date_str = date.strftime('%Y-%m-%d')
                        else:
                            date_str = str(date)
                        
                        # Extract rating values
                        action = row.get('Action', '')
                        rating_change = row.get('Rating Change', '')
                        price_target_change = row.get('Price Target Change', '')
                        
                        # Parse current rating from Rating Change
                        current_rating = ''
                        if ' → ' in rating_change:
                            current_rating = rating_change.split(' → ')[1]
                            logger.debug(f"Extracted current rating: {current_rating} from {rating_change}")
                        else:
                            current_rating = rating_change
                        
                        # Parse current price target from Price Target Change
                        current_price_target = 0
                        if price_target_change:
                            if ' → ' in price_target_change:
                                target_str = price_target_change.split(' → ')[1].replace('$', '').strip()
                                logger.debug(f"Extracted target price: {target_str} from {price_target_change}")
                                try:
                                    current_price_target = float(target_str)
                                except Exception as e:
                                    logger.warning(f"Failed to convert price target '{target_str}' to float: {e}")
                            else:
                                target_str = price_target_change.replace('$', '').strip()
                                try:
                                    current_price_target = float(target_str)
                                except Exception as e:
                                    logger.warning(f"Failed to convert price target '{target_str}' to float: {e}")
                        
                        logger.debug(f"Creating Analyst node for {analyst} with rating {current_rating} and target ${current_price_target}")
                        # Create Analyst node connected to Analysis
                        session.run(
                            """
                            MATCH (a:Analysis {name: $analysis_name})-[:RATES]->(s:Stock {ticker: $ticker})
                            MERGE (r:Analyst {name: $analyst, ticker: $ticker})
                            SET r.date = $date,
                                r.action = $action,
                                r.rating_change = $rating_change,
                                r.current_rating = $current_rating,
                                r.price_target_change = $price_target_change,
                                r.current_price_target = $current_price_target
                            MERGE (r)-[:BELONGS_TO]->(a)
                            """,
                            ticker=ticker,
                            analysis_name=analysis_node_name,
                            analyst=analyst,
                            date=date_str,
                            action=action,
                            rating_change=rating_change,
                            current_rating=current_rating,
                            price_target_change=price_target_change,
                            current_price_target=current_price_target
                        )
                        analyst_count += 1
                        logger.debug(f"Created Analyst node for {analyst}")
                    except Exception as e:
                        logger.error(f"Error creating analyst node for {analyst}: {e}")
                
                logger.info(f"Completed saving analyst ratings: {analyst_count} created, {skipped_count} skipped")
            else:
                # If we can't group by analyst, process each row as is
                logger.info("Processing analyst ratings without grouping (missing Analyst or Date column)")
                logger.info(f"Available columns: {analysts_ratings.columns.tolist()}")
                
                row_count = 0
                skipped_count = 0
                
                for idx, row in analysts_ratings.iterrows():
                    date = row.get('Date')
                    analyst = row.get('Analyst', '')
                    
                    if pd.isna(date) or pd.isna(analyst):
                        logger.debug(f"Skipping row at index {idx} due to missing analyst name or date")
                        skipped_count += 1
                        continue
                    
                    try:
                        # Convert date to string format if it's a datetime
                        if hasattr(date, 'strftime'):
                            date_str = date.strftime('%Y-%m-%d')
                        else:
                            date_str = str(date)
                        
                        action = row.get('Action', '')
                        rating_change = row.get('Rating Change', '')
                        price_target_change = row.get('Price Target Change', '')
                        
                        logger.debug(f"Creating Analyst node for {analyst} on {date_str}")
                        # Create Analyst node connected to Analysis
                        session.run(
                            """
                            MATCH (a:Analysis {name: $analysis_name})-[:RATES]->(s:Stock {ticker: $ticker})
                            MERGE (r:Analyst {name: $analyst, ticker: $ticker})
                            SET r.date = $date,
                                r.action = $action,
                                r.rating_change = $rating_change,
                                r.price_target_change = $price_target_change
                            MERGE (r)-[:BELONGS_TO]->(a)
                            """,
                            ticker=ticker,
                            analysis_name=analysis_node_name,
                            date=date_str,
                            analyst=analyst,
                            action=action,
                            rating_change=rating_change,
                            price_target_change=price_target_change
                        )
                        row_count += 1
                        logger.debug(f"Created Analyst node for {analyst}")
                    except Exception as e:
                        logger.error(f"Error creating analyst node for {analyst}: {e}")
                
                logger.info(f"Completed saving analyst ratings without grouping: {row_count} created, {skipped_count} skipped")
                
        except Exception as e:
            logger.error(f"Error saving analyst ratings: {e}")
            logger.info("Trying fallback approach - connections through Analysis node")
            
            try:
                logger.info(f"Processing {len(analysts_ratings)} ratings using fallback approach")
                fallback_count = 0
                
                for idx, row in analysts_ratings.iterrows():
                    date = row.get('Date')
                    analyst = row.get('Analyst', '')
                    
                    if pd.isna(date) or pd.isna(analyst):
                        continue
                    
                    try:
                        # Convert date to string format if it's a datetime
                        if hasattr(date, 'strftime'):
                            date_str = date.strftime('%Y-%m-%d')
                        else:
                            date_str = str(date)
                        
                        action = row.get('Action', '')
                        rating_change = row.get('Rating Change', '')
                        price_target_change = row.get('Price Target Change', '')
                        
                        logger.debug(f"Creating Analyst node with fallback approach for {analyst}")
                        # Create Analyst node with connection through Analysis node
                        session.run(
                            """
                            MATCH (s:Stock {ticker: $ticker})
                            MERGE (a:Analysis {name: $analysis_name})
                            MERGE (a)-[:RATES]->(s)
                            MERGE (r:Analyst {name: $analyst, ticker: $ticker})
                            SET r.date = $date,
                                r.action = $action,
                                r.rating_change = $rating_change,
                                r.price_target_change = $price_target_change
                            MERGE (r)-[:BELONGS_TO]->(a)
                            """,
                            ticker=ticker,
                            analysis_name=analysis_node_name,
                            date=date_str,
                            analyst=analyst,
                            action=action,
                            rating_change=rating_change,
                            price_target_change=price_target_change
                        )
                        fallback_count += 1
                        logger.debug(f"Created analyst node using fallback approach for {analyst}")
                    except Exception as sub_e:
                        logger.error(f"Error in fallback for analyst {analyst}: {sub_e}")
                
                logger.info(f"Completed fallback approach: {fallback_count} analysts created")
            except Exception as fallback_e:
                logger.error(f"Fallback for analyst ratings also failed: {fallback_e}")
    
    def _save_news_sentiment(self, session, ticker, news_sentiment):
        """
        Save news sentiment to Neo4j.
        
        Args:
            session: The Neo4j session
            ticker: The stock ticker symbol
            news_sentiment: DataFrame of news sentiment
        """
        logger.info(f"Saving news sentiment for {ticker}")
        
        if news_sentiment is None or news_sentiment.empty:
            logger.warning(f"No news sentiment data available for {ticker}")
            return
            
        # Create NewsFeed node and connect to stock
        news_file_path = f"data/{ticker}/news_sentiment.csv"
        news_feed_name = f"News Feed - {ticker}"
        
        try:
            logger.info(f"Creating NewsFeed node for {ticker}")
            session.run(
                """
                MATCH (s:Stock {ticker: $ticker})
                MERGE (nf:NewsFeed {name: $news_feed_name})
                SET nf.data_file = $file_path
                MERGE (nf)-[:ABOUT]->(s)
                """,
                ticker=ticker,
                news_feed_name=news_feed_name,
                file_path=news_file_path
            )
            logger.info(f"NewsFeed node created: {news_feed_name} with path {news_file_path}")
            
            # Save the news DataFrame to CSV
            logger.debug(f"Saving news data to {news_file_path}")
            os.makedirs(os.path.dirname(news_file_path), exist_ok=True)
            news_sentiment.to_csv(news_file_path, index=False)
            logger.info(f"Saved {len(news_sentiment)} news items to CSV")
                
            # Optional: Create individual News nodes connected to the NewsFeed
            logger.info(f"Processing {len(news_sentiment)} news items for individual nodes")
            news_count = 0
            skipped_count = 0
            
            for idx, row in news_sentiment.iterrows():
                title = row.get('title')
                if pd.isna(title):
                    logger.debug(f"Skipping news at index {idx} due to missing title")
                    skipped_count += 1
                    continue
                
                try:
                    date = row.get('publishedAt')
                    # Convert date to string format if it's a datetime
                    if hasattr(date, 'strftime'):
                        date_str = date.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date)
                    
                    source = row.get('source', {}).get('name', '') if isinstance(row.get('source'), dict) else ''
                    description = row.get('description', '')
                    url = row.get('url', '')
                    sentiment = float(row.get('sentiment', 0)) if not pd.isna(row.get('sentiment')) else 0
                    
                    logger.debug(f"Creating News node for: {title[:30]}... with sentiment {sentiment}")
                    # Create News node connected to NewsFeed
                    session.run(
                        """
                        MATCH (nf:NewsFeed {name: $news_feed_name})-[:ABOUT]->(s:Stock {ticker: $ticker})
                        MERGE (n:News {
                            title: $title,
                            date: $date,
                            source: $source
                        })
                        SET n.description = $description,
                            n.url = $url,
                            n.sentiment = $sentiment
                        MERGE (n)-[:BELONGS_TO]->(nf)
                        """,
                        ticker=ticker,
                        news_feed_name=news_feed_name,
                        title=title,
                        date=date_str,
                        source=source,
                        description=description,
                        url=url,
                        sentiment=sentiment
                    )
                    news_count += 1
                    logger.debug(f"Created News node for article: {title[:30]}...")
                except Exception as e:
                    logger.error(f"Error creating News node for {title[:30]}...: {e}")
            
            logger.info(f"Completed saving news sentiment: {news_count} created, {skipped_count} skipped")
        except Exception as e:
            logger.error(f"Failed to save news sentiment for {ticker}: {e}") 
"""Main module for financial data analysis and RDF storage."""

import warnings
import sys
warnings.filterwarnings('ignore')
from packages.data_analyzer.financial_data_analyzer import FinancialDataAnalyzer
from packages.data_storage.neo4j_manager import Neo4jManager

def add_ticker_to_database(ticker):
    """
    Add a single stock ticker to the Neo4j database.
    
    This function:
    1. Initializes a FinancialDataAnalyzer with the specified ticker
    2. Runs analysis to gather financial data (price, insiders, news, etc.)
    3. Saves the collected data to local files
    4. Loads the saved data and stores it in Neo4j
    5. Maintains existing data in the database
    
    Args:
        ticker (str): The stock ticker symbol to add (e.g., "AAPL", "MSFT")
        
    Returns:
        tuple: (success, message) where success is a boolean indicating if the operation succeeded,
               and message is a descriptive string about the result
    """
    try:
        # Initialize analyzer with just the new ticker
        analyzer = FinancialDataAnalyzer([ticker])
        
        # Run analysis to gather and save data to files
        analyzer.run_analysis()
        
        # Now save this ticker's data to Neo4j without clearing the database
        saved_data = analyzer.data_saver.load_saved_data(ticker)
        
        if saved_data:
            analyzer.save_to_neo4j(ticker, saved_data)
        else:
            # Fallback to the general save method
            analyzer.save_to_neo4j()
            
        # Close connections
        analyzer.close()
        return True, f"Successfully added {ticker} to the database"
    except Exception as e:
        return False, f"Error adding {ticker}: {e}"

def clear_database():
    """
    Clear the entire Neo4j database, removing all nodes and relationships.
    
    This function:
    1. Creates a direct connection to the Neo4j database
    2. Executes a Cypher query to remove all nodes and relationships
    3. Verifies that the database was successfully cleared
    4. Attempts a second clearing if needed
    
    Returns:
        tuple: (success, message) where success is a boolean indicating if the operation succeeded,
               and message is a descriptive string about the result
    """
    try:
        print("Starting database clearing process...")
        # Create a direct Neo4jManager instance instead of going through FinancialDataAnalyzer
        neo4j_manager = Neo4jManager()
        
        # Clear the database
        print("Executing clear_database method...")
        neo4j_manager.clear_database()
        
        # Verify the database was cleared
        with neo4j_manager.driver.session(database=neo4j_manager.database) as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            remaining = result.single()["count"]
            print(f"Verification: {remaining} nodes remain after clearing")
            
            if remaining > 0:
                print("Warning: Database not fully cleared, attempting again...")
                session.run("MATCH (n) DETACH DELETE n")
                
                # Verify again
                result = session.run("MATCH (n) RETURN count(n) as count")
                remaining = result.single()["count"]
                print(f"Second verification: {remaining} nodes remain after clearing")
        
        # Close the connection
        neo4j_manager.close()
        
        return True, "Database successfully cleared"
    except Exception as e:
        print(f"Error in clear_database: {e}")
        return False, f"Error clearing database: {e}"

def main():
    """
    Main entry point for the application.
    
    This function:
    1. Checks for command line arguments to determine operation mode
    2. Launches the web interface if --web flag is provided
    3. Otherwise processes specified stock tickers for analysis
    4. Gathers financial data and saves it to Neo4j
    
    Returns:
        int: 0 for successful execution, 1 for errors
    """
    try:
        # Check for web interface flag
        if  "--web" in sys.argv:
            # Remove the flag so it doesn't interfere with other arguments
            sys.argv.remove("--web")
            # Run the web interface
            run_web_interface()
            return 0
        
        # Get tickers from command line arguments if provided
        custom_tickers = sys.argv[1:] if len(sys.argv) > 1 else None
        
        # Initialize analyzer with custom tickers or use defaults from config
        analyzer = FinancialDataAnalyzer(custom_tickers)
        analyzer.run_analysis()
        
        # Save to Neo4j without clearing the database
        analyzer.save_to_neo4j()
        
        analyzer.close()  # Close connections properly
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1
    return 0

def run_web_interface():
    """
    Run the Streamlit web interface for interactive data visualization and management.
    
    This function:
    1. Imports necessary modules for web interface
    2. Locates the frontend.py file in the current directory
    3. Launches Streamlit with the frontend file
    4. Handles errors and provides feedback
    
    Raises:
        ImportError: If Streamlit is not installed
        Exception: For other errors during web interface startup
    """
    print("Starting web interface. Please wait...")
    try:
        # We import here to avoid unnecessary dependencies when running in CLI mode
        import os
        import subprocess
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run Streamlit
        subprocess.run(["streamlit", "run", os.path.join(current_dir, "frontend.py")])
    except ImportError:
        print("Streamlit is not installed. Please install it with 'pip install streamlit'")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting web interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    exit(main())

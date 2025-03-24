"""Main module for financial data analysis and RDF storage."""

import warnings
import sys
warnings.filterwarnings('ignore')
from packages.data_analyzer.financial_data_analyzer import FinancialDataAnalyzer
from packages.data_storage.neo4j_manager import Neo4jManager

def add_ticker_to_database(ticker):
    """Add a single ticker to the database"""
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
    """Clear the entire Neo4j database"""
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
    """Run the Streamlit web interface"""
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

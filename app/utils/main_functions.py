"""Simplified versions of main.py functions for use as fallbacks."""

import streamlit as st
from components.database import direct_clear_database

def add_ticker_to_database_fallback(ticker):
    """Simplified version of add_ticker_to_database that shows an error."""
    st.error(f"""
    Could not add ticker {ticker} to database. 
    The main module could not be imported.
    
    This is a simplified fallback function.
    
    Please run the application from the project root with:
    ```
    python run.py
    ```
    """)
    return False, f"Error adding {ticker}: Main module could not be imported"

def clear_database_fallback():
    """Simplified version that calls the direct_clear_database function."""
    st.warning("Using direct database clearing method as fallback.")
    return direct_clear_database() 
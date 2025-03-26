"""Database operations wrapper functions."""

import os
import sys
import streamlit as st
from .main_functions import add_ticker_to_database_fallback, clear_database_fallback

# Try to import from the parent directory
try:
    # Get the parent directory
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
    sys.path.insert(0, parent_dir)
    from main import add_ticker_to_database as main_add_ticker
    from main import clear_database as main_clear_database
    MAIN_IMPORTS_SUCCEEDED = True
except ImportError:
    MAIN_IMPORTS_SUCCEEDED = False
    st.warning("Failed to import from main module. Using fallback functions.")

def add_ticker_to_database(ticker):
    """Wrapper for the add_ticker_to_database function."""
    if MAIN_IMPORTS_SUCCEEDED:
        # Use the imported function
        return main_add_ticker(ticker)
    else:
        # Use the fallback function
        return add_ticker_to_database_fallback(ticker)

def clear_database():
    """Wrapper for the clear_database function."""
    if MAIN_IMPORTS_SUCCEEDED:
        # Use the imported function
        return main_clear_database()
    else:
        # Use the fallback function
        return clear_database_fallback() 
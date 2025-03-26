"""Configuration utilities for the application."""

import os
import sys
import streamlit as st
import importlib.util

def get_default_stock_tickers():
    """
    Try to load DEFAULT_STOCK_TICKER from the main config.py file.
    If it fails, try the local config.py in the app directory.
    If that fails too, return a fallback list of default tickers.
    """
    # First try the root config
    try:
        # Get the parent directory (project root)
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
        sys.path.insert(0, parent_dir)
        
        # Try to import from config.py in the root
        from config import DEFAULT_STOCK_TICKER
        return DEFAULT_STOCK_TICKER
    except ImportError:
        # Root import failed, try the local config
        pass
    
    # Now try the local app/config.py
    try:
        # Get the app directory path
        app_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(app_dir, 'config.py')
        
        # Use importlib to load the module from path
        spec = importlib.util.spec_from_file_location('app_config', config_path)
        app_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_config)
        
        st.info("Using local config.py for default tickers.")
        return app_config.DEFAULT_STOCK_TICKER
    except (ImportError, AttributeError, FileNotFoundError):
        # Both imports failed, use hardcoded fallback
        st.warning("Using hardcoded fallback stock tickers.")
        return ["C", "AAPL", "MSFT", "GOOGL"] 
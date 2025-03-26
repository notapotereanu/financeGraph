"""Utility functions for data formatting and display."""

import json
import pandas as pd

def format_json_for_display(json_data):
    """Format JSON data for readable display."""
    try:
        if isinstance(json_data, str):
            # Try to parse the string as JSON
            parsed_data = json.loads(json_data)
            return json.dumps(parsed_data, indent=2)
        elif isinstance(json_data, (dict, list)):
            # Already a Python object, just format it
            return json.dumps(json_data, indent=2)
        else:
            # Return as string if not JSON
            return str(json_data)
    except:
        # If parsing fails, return the original string
        return str(json_data)

def format_property_table(properties):
    """Format a dictionary of properties into a DataFrame for display."""
    if not properties:
        return pd.DataFrame()
        
    # Create a DataFrame from the properties
    df = pd.DataFrame([properties])
    
    # Format any nested JSON
    for col in df.columns:
        if isinstance(df[col].iloc[0], (dict, list)):
            df[col] = df[col].apply(format_json_for_display)
    
    return df

def format_relationship_label(rel_type, shares=None):
    """Format a relationship label, including shares if available."""
    if shares:
        return f"{rel_type} ({shares} shares)"
    return rel_type

def truncate_text(text, max_length=50):
    """Truncate text to a maximum length with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..." 
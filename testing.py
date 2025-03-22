import yfinance as yf
import pandas as pd

def get_top_managers(ticker):
    """
    Get information about top managers for a given ticker using yfinance
    """
    try:
        # Get company info
        company = yf.Ticker(ticker)
        info = company.info
        
        # Get major holders
        major_holders = company.major_holders
        
        # Get institutional holders
        institutional_holders = company.institutional_holders
        
        # Get company officers
        officers = company.info.get('companyOfficers', [])
        
        print(f"\nCompany Information for {ticker}:")
        print("-" * 80)
        print(f"Company Name: {info.get('longName', 'N/A')}")
        print(f"Sector: {info.get('sector', 'N/A')}")
        print(f"Industry: {info.get('industry', 'N/A')}")
        print("-" * 80)
        
        print("\nTop Executives:")
        print("-" * 80)
        for officer in officers[:10]:  # Show top 10 officers
            print(f"Name: {officer.get('name', 'N/A')}")
            print(f"Title: {officer.get('title', 'N/A')}")
            print(f"Year Born: {officer.get('yearBorn', 'N/A')}")
            print("-" * 80)
        
        print("\nMajor Holders:")
        print("-" * 80)
        if major_holders is not None:
            print(major_holders)
        
        print("\nInstitutional Holders:")
        print("-" * 80)
        if institutional_holders is not None:
            print(institutional_holders)
            
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")

# Example usage
get_top_managers('AAPL')

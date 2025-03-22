import yfinance as yf
import pandas as pd
import time
from requests.exceptions import Timeout, HTTPError
import random

def get_top_managers(ticker, max_retries=3, timeout=60):
    """
    Get information about top managers for a given ticker using yfinance
    with retry logic for handling timeouts and rate limits
    """
    for attempt in range(max_retries):
        try:
            # Add random delay between attempts to avoid rate limiting
            if attempt > 0:
                delay = min(300, (2 ** attempt) + random.uniform(1, 5))
                print(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
            
            # Get company info
            company = yf.Ticker(ticker)
            
            # Add delay between API calls
            time.sleep(2)
            
            # Get company info
            info = company.info
            
            # Add delay between API calls
            time.sleep(2)
            
            # Get major holders
            major_holders = company.major_holders
            
            # Add delay between API calls
            time.sleep(2)
            
            # Get institutional holders
            institutional_holders = company.institutional_holders
            
            # Get company officers
            officers = company.info.get('companyOfficers', [])
            
            print(f"\nCompany Information for {ticker}:")
            print("-" * 80)
            print(f"Company Name: {info.get('longName', 'N/A')}")
            print(f"Sector: {info.get('sector', 'N/A')}")
            print(f"Industry: {info.get('industry', 'N/A')}")
            print(f"Full Time Employees: {info.get('fullTimeEmployees', 'N/A')}")
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
            
            return  # Success, exit the function
            
        except Timeout:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} timed out. Retrying...")
            else:
                print(f"Error: All {max_retries} attempts timed out. Please try again later.")
        except HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Waiting before retry...")
                else:
                    print(f"Error: Rate limit exceeded after {max_retries} attempts. Please try again later.")
            else:
                print(f"HTTP Error: {str(e)}")
                return
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return

# Example usage
get_top_managers('AAPL') 
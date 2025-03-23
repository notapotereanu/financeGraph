import requests

def get_competitors(ticker):
    """
    Returns a list of competitor company names and their tickers for the given ticker.
    """
    # First get competitor tickers
    url = f"https://finnhub.io/api/v1/stock/peers?symbol={ticker}&token=cvf7sr9r01qjugsgj8a0cvf7sr9r01qjugsgj8ag"
    response = requests.get(url)
    
    if response.status_code == 200:
        competitor_tickers = response.json()
        if competitor_tickers and ticker in competitor_tickers:
            competitor_tickers.remove(ticker)
            
        # Get company profile for each competitor ticker
        competitors = []
        for comp_ticker in competitor_tickers:
            profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={comp_ticker}&token=cvf7sr9r01qjugsgj8a0cvf7sr9r01qjugsgj8ag"
            profile_response = requests.get(profile_url)
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                if profile and 'name' in profile:
                    competitors.append({
                        'ticker': comp_ticker,
                        'name': profile['name']
                    })
                    
        return competitors
    else:
        print(f"Error in request: {response.status_code}")
        return None
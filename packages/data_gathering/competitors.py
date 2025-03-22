import requests

def get_competitors(ticker):
    """
    Restituisce una lista di ticker dei concorrenti per il ticker fornito.
    """
    url = f"https://finnhub.io/api/v1/stock/peers?symbol={ticker}&token=cvf7sr9r01qjugsgj8a0cvf7sr9r01qjugsgj8ag"
    response = requests.get(url)
    
    if response.status_code == 200:
        competitors = response.json()  # La risposta è una lista di ticker concorrenti
        if competitors and ticker in competitors:
                competitors.remove(ticker)
        return competitors
    else:
        print(f"Errore nella richiesta: {response.status_code}")
        return None
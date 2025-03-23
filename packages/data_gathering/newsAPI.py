import requests
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()

API_KEY = "4f9a2b0c1efd40318cdf751d5b7444f1"
BASE_URL = "https://newsapi.org/v2/everything"

def newsAPI_get_df(keyword, num_articles=100):
    """Fetches the latest news articles from the past month and performs sentiment analysis."""
    
    today = datetime.utcnow().date()
    last_month = today - timedelta(days=28)

    params = {
        "q": keyword,
        "from": last_month,
        "to": today,
        "sortBy": "publishedAt",
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": num_articles  #
    }
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])
        
        news_data = []
        
        for article in articles:
            title = article["title"]
            sentiment_score = sia.polarity_scores(title)["compound"]
            sentiment = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
            
            news_data.append({
                "Title": title,
                "Published At": article["publishedAt"],
                "URL": article["url"],
                "Sentiment": sentiment,
                "Sentiment Score": sentiment_score
            })
        
        df = pd.DataFrame(news_data)
        return df
    else:
        print(f"Error News Setiment: {response.status_code} - {response.json()}")
        return None
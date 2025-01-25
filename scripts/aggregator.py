import requests
from datetime import datetime, timedelta
from database import fetch_articles_by_date, store_daily_aggregate

def compute_daily_average_sentiment(date_str):
    articles = fetch_articles_by_date(date_str)
    if not articles:
        return 0.0
    
    total_score = 0.0
    for article in articles:
        total_score += article["sentiment_score"]

    avg_score = total_score / len(articles)
    return avg_score

# returns bitcoin price using coingecko's api
def fetch_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["bitcoin"]["usd"]

def aggregate_daily_data():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    date_str = yesterday.isoformat()

    avg_sentiment = compute_daily_average_sentiment(date_str)

    btc_price = fetch_btc_price()

    store_daily_aggregate(date_str, avg_sentiment, btc_price)
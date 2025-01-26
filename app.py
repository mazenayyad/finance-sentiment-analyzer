from flask import Flask, render_template
from scripts.scraper import scrape
from scripts.analysis import init_models, summarize_text, analyze_sentiment, aggregate_numeric_scores
from database import insert_articles, init_db, fetch_articles_by_date, fetch_finance_daily
from datetime import datetime
import threading
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

BITCOIN_RSS_URL = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"

SCRAPE_DONE = False

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

def long_scrape():
    global SCRAPE_DONE

    articles = scrape(BITCOIN_RSS_URL)

    # summarize each article
    for article in articles:
        article["summary"] = summarize_text(article["content"])

    # perform sentiment analysis
    analyzed_articles = analyze_sentiment(articles)

    # insert new articles in database
    for article in articles:
        insert_articles(
            title=article["title"],
            source=article["source"],
            pub_date=article["pub_date"],
            final_url=article["final_url"],
            summary=article["summary"],
            sentiment_score=article["sentiment_score"],
            sentiment_label=article["sentiment_label"]
        )

    SCRAPE_DONE = True

@app.route("/loading")
def loading():
    global SCRAPE_DONE
    SCRAPE_DONE = False
    thread = threading.Thread(target=long_scrape)
    thread.start()
    return render_template("loading.html")

@app.route("/check_status")
def check_status():
    global SCRAPE_DONE
    if SCRAPE_DONE:
        return "done"
    else:
        return "not done"

@app.route("/results")
def results():
    # fetch all articles from todays date
    utc_today_str = datetime.utcnow().date().isoformat()
    todays_articles = fetch_articles_by_date(utc_today_str)

    agg_label, agg_score = aggregate_numeric_scores(todays_articles)

    last_updated = datetime.utcnow().strftime("%d %b, %Y %H:%M UTC")

    daily_data = fetch_finance_daily()

    if not daily_data:
        chart_html = "<p>No historical data available yet.</p>"
    else:
        # convert daily data to a pandas dataframe
        df = pd.DataFrame(daily_data)

        # creating a figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # primary y-axis (avg sentiment)
        fig.add_trace(
            go.Scatter(
            x = df["date_str"],
            y = df["avg_sentiment"],
            name = "Average Sentiment",
            mode = "lines+markers"
            ),
            secondary_y = False
        )

        # seconday y-axis (btc price)
        fig.add_trace(
            go.Scatter(
            x = df["date_str"],
            y = df["btc_price"],
            name = "Bitcoin Price (USD)",
            mode = "lines+markers",
            line_color = "orange"
            ),
            secondary_y = True
        )

        # customizing layout and axis
        fig.update_layout(
            title = "Daily Sentiment vs. BTC Price - (Last 30 days)",
            hovermode = "x unified"
        )

        # sentiment - primary y-axis
        fig.update_yaxes(
            title_text = "Average Sentiment (-100 to 100)",
            range = [-100, 100], # fixed range
            secondary_y = False
        )

        # btc price - secondary y-axis
        fig.update_yaxes(
            title_text = "BTC Price (USD)",
            secondary_y = True
        )

        fig.update_xaxes(title_text="Date")

        # convert to html snippet. returns only the div and script for the chart, not a full HTML document
        chart_html = fig.to_html(full_html=False)

    return render_template("results.html", articles=todays_articles, agg_label=agg_label, agg_score=agg_score, last_updated=last_updated, chart_html=chart_html)

if __name__ == "__main__":
    init_db()
    # load models after importing to not clash, avoiding "spawn" errors
    init_models() 
    app.run(debug=True)
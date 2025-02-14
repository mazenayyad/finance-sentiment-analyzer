from flask import Flask, render_template, request
from scripts.scraper import scrape
from scripts.analysis import init_models, summarize_text, analyze_sentiment, aggregate_numeric_scores
from database import insert_articles, init_db, fetch_articles_by_date, fetch_finance_daily
from datetime import datetime, timedelta
import threading
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from scripts.aggregator import aggregate_daily_data

BITCOIN_RSS_URL = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"
LAST_AGGREGATED_DATE = None
LAST_SCRAPE_TIME = None
SCRAPE_INTERVAL_HOURS = 8

def periodic_scrape_thread():
    global LAST_SCRAPE_TIME
    while True:
        try:
            # scrape articles
            articles = scrape(BITCOIN_RSS_URL)

            # summarize each article
            for article in articles:
                article["summary"] = summarize_text(article["content"])

            # analyze sentiment
            analyzed_articles = analyze_sentiment(articles)

            # insert into db
            for article in analyzed_articles:
                insert_articles(
                    title=article["title"],
                    source=article["source"],
                    pub_date=article["pub_date"],
                    final_url=article["final_url"],
                    summary=article["summary"],
                    sentiment_score=article["sentiment_score"],
                    sentiment_label=article["sentiment_label"]
                )

            # after successful scraping
            LAST_SCRAPE_TIME = datetime.utcnow()
        except Exception as e:
            print(f"Error occurred while periodically scraping: {e}")
        time.sleep(SCRAPE_INTERVAL_HOURS * 3600) # sleep for 8 hrs

def daily_aggregator_thread():
    global LAST_AGGREGATED_DATE

    while True:
        current_date = datetime.utcnow().date()

        # on the first run, just set LAST_AGGREGATED_DATE to current_date. to not aggregate yesterday's data on the first run
        if LAST_AGGREGATED_DATE is None:
            LAST_AGGREGATED_DATE = current_date

        # if the date has changed since last check -> we crossed midnight
        if current_date != LAST_AGGREGATED_DATE:
            try:
                aggregate_daily_data()
            except Exception as e:
                print(f"[Aggregator Thread] Error aggregating data for yesterday: {e}")
            
            # update global so it doesn't repeat for same day
            LAST_AGGREGATED_DATE = current_date

        time.sleep(1800) # sleep for 30 min



app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/loading")
def loading():
    return render_template("loading.html")

@app.route("/results")
def results():
    global LAST_SCRAPE_TIME, SCRAPE_INTERVAL_HOURS
    
    today_str = datetime.utcnow().date().isoformat()

    # read the 'timeframe' parameter from the URL
    # if ?timeframe= is missing, default to "today"
    timeframe = request.args.get("timeframe", "today")

    # if user requested "yesterday"
    if timeframe == "yesterday":
        yesterday_str = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
        articles_for_that_day = fetch_articles_by_date(yesterday_str)

        date_label = "yesterday" # for display in UI

        # since "yesterday" is a past date, there's no concept of next scrape time
        time_until_next_str = "N/A (past date)"
    else:
        # otherwise, fetch "today" by default
        articles_for_that_day = fetch_articles_by_date(today_str)

        date_label = "today"

        # will show how long until next scrape, if we know the last scrape time
        if LAST_SCRAPE_TIME is not None:
            next_scrape_dt = LAST_SCRAPE_TIME + timedelta(hours=SCRAPE_INTERVAL_HOURS)
            now_utc = datetime.utcnow()
            time_remaining = next_scrape_dt - now_utc

            if time_remaining.total_seconds() > 0:
                hours_left = int(time_remaining.total_seconds() // 3600)
                minutes_left = int(time_remaining.total_seconds() % 3600 // 60)
                time_until_next_str = f"{hours_left}h {minutes_left}m"
            else:
                # if it's already past schedule time but thread hasn't run yet
                time_until_next_str = "Currently analyzing..."
        else:
            time_until_next_str = "Error: This is the first run/first scrape. Please wait until the scrape is done then refresh."

    agg_label, agg_score = aggregate_numeric_scores(articles_for_that_day)

    if LAST_SCRAPE_TIME is not None:
        last_updated = LAST_SCRAPE_TIME.strftime("%d %b, %Y %H:%M UTC")
    else:
        last_updated = "Never (no data yet)"

    daily_data = fetch_finance_daily()
    if not daily_data:
        chart_html = ""
    else:
        # convert daily data to a pandas dataframe
        df = pd.DataFrame(daily_data)

        # creating a figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # primary y-axis (btc price)
        fig.add_trace(
            go.Scatter(
            x = df["date_str"],
            y = df["btc_price"],
            name = "Bitcoin Price (USD)",
            mode = "lines+markers",
            line_color = "orange"
            ),
            secondary_y = False
        )

        # secondary y-axis (avg sentiment)
        fig.add_trace(
            go.Scatter(
            x = df["date_str"],
            y = df["avg_sentiment"],
            marker={'size':6},
            line={'width':2},
            name = "Average Sentiment",
            mode = "lines+markers"
            ),
            secondary_y = True
        )

        # customizing layout and axis
        fig.update_layout(
            template="plotly_dark",
            title={'text':"Daily Sentiment vs. BTC Price",'x':0.5},
            margin={'l':50,'r':50,'t':50,'b':50},
            hovermode = "x unified",
            font = {"color": "#ffffff", 'size':12},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend={'x':0.02,'y':0.98,'bgcolor':"rgba(0,0,0,0)"},
            hoverlabel={'bgcolor':"rgba(0, 0, 0, 0.7)",'font_color':"#ffffff"}
        )

        # btc price - primary y-axis
        fig.update_yaxes(
            title_text = "BTC Price (USD)",
            tickformat= ",.0f",
            secondary_y = False
        )

        # sentiment - secondary y-axis
        fig.update_yaxes(
            title_text = "Average Sentiment (-100 to 100)",
            range = [-110, 110], # fixed range. so 0 sentiment can be visible
            secondary_y = True
        )

        fig.update_xaxes(
            title_text="Date",
            tickformat="%b %d", # ex: Jan 31
            dtick = "D1" # daily ticks
        )

        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Price: $%{y}<extra></extra>",
            selector={"name": "Bitcoin Price (USD)"}
        )

        fig.update_traces(
            hovertemplate="Sentiment: %{y}<extra></extra>",
            selector={"name": "Average Sentiment"}
        )

        # convert to html snippet. returns only the div and script for the chart, not a full HTML document
        chart_html = fig.to_html(
            full_html=False,
            config={'displaylogo':False,'scrollZoom':False,'displayModeBar':False}
        )

    return render_template("results.html", articles=articles_for_that_day, agg_label=agg_label, agg_score=agg_score, last_updated=last_updated, time_until_next=time_until_next_str, daily_data=daily_data, chart_html=chart_html, timeframe=timeframe, date_label=date_label)

if __name__ == "__main__":
    init_db()
    init_models()

    scrape_thread = threading.Thread(target=periodic_scrape_thread, daemon=True)
    scrape_thread.start()

    agg_thread = threading.Thread(target=daily_aggregator_thread, daemon=True)
    agg_thread.start()

    # run Flask in debug mode for local testing
    app.run(debug=True, host="0.0.0.0", port=5001)
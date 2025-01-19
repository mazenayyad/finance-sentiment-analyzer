from flask import Flask, render_template
from scripts.scraper import scrape
from scripts.analysis import init_models, summarize_text, analyze_sentiment, aggregate_numeric_scores
from database import insert_articles, init_db

BITCOIN_RSS_URL = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/results")
def results():
    articles = scrape(BITCOIN_RSS_URL)

    # summarize each article
    for article in articles:
        article["summary"] = summarize_text(article["content"])

    # perform sentiment analysis
    analyzed_articles = analyze_sentiment(articles)
    agg_label, agg_score = aggregate_numeric_scores(analyzed_articles)

    # insert new articles in database
    for article in articles:
        insert_articles(
            title=article["title"],
            source=article["source"],
            publish_date=article["pub_date"],
            final_url=article["final_url"],
            summary=article["summary"],
            sentiment_score=article["sentiment_score"],
            sentiment_label=article["sentiment_label"]
        )

    return render_template("results.html", articles=analyzed_articles, agg_label=agg_label, agg_score=agg_score)


if __name__ == "__main__":
    init_db()
    # load models after importing to not clash, avoiding "spawn" errors
    init_models() 
    app.run(debug=True)
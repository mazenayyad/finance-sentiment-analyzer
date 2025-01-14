from flask import Flask, render_template
from scripts.scraper import scrape
from scripts.analysis import init_models, summarize_text, analyze_sentiment, aggregate_numeric_scores

BITCOIN_RSS_URL = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"

app = Flask(__name__)

@app.route("/")
def home():
    """
    Show a simple landing page with a link to /results.
    """
    return render_template("index.html")


@app.route("/results")
def results():
    """
    When the user hits /results, we'll:
    1) Scrape articles
    2) Summarize them
    3) Analyze sentiment
    4) Aggregate scores
    5) Render everything in results.html
    """
    articles = scrape(BITCOIN_RSS_URL)

    # summarize each article
    for article in articles:
        article["summary"] = summarize_text(article["content"])

    # perform sentiment analysis
    analyzed_articles = analyze_sentiment(articles)
    agg_label, agg_score = aggregate_numeric_scores(analyzed_articles)

    return render_template("results.html", articles=analyzed_articles, agg_label=agg_label, agg_score=agg_score)


if __name__ == "__main__":
    # load models after importing to not clash, avoiding "spawn" errors
    init_models() 
    app.run(debug=True)
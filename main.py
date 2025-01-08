from scripts.scraper import scrape
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# arg is articles which is a list of dictionaries of titles and content. so far its only doing title
def analyze_sentiment(articles):
    # load finBERT
    tokenizer = BertTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    model = BertForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

    # analyze sentiment for each article
    for article in articles:
        title = article["title"]

        # tokenize the title for the model
        inputs = tokenizer(title, return_tensors="pt", padding=True, truncation=True, max_length=512)

        # send the tokenized title to the model
        outputs = model(**inputs)

        # extract logits from model (raw data)
        logits = outputs.logits

        # softmax to obtain human understandable probabilities
        probabilities = torch.nn.functional.softmax(logits, dim=1)

        # extract the 3 numbers
        p_neu, p_pos, p_neg = probabilities[0].tolist()

        # -100 to 100 sentiment score
        score = 100 * (p_pos - p_neg)

        article["sentiment_score"] = score # add sentiment score to the article

        # argmax to obtain the most likely class (negative neutral or positive)
        predicted_class = torch.argmax(probabilities, dim=1).item()

        sentiment = ['neutral', 'positive', 'negative'][predicted_class]
        article["sentiment_label"] = sentiment # add sentiment to the article

    return articles

def aggregate_numeric_scores(articles):
    if not articles:
        # if no articles, return something default
        return "neutral", 0.0
    
    total_score = 0.0
    for article in articles:
        total_score += article["sentiment_score"]

    avg_score = total_score / len(articles)

    # decide overall label
    if avg_score > 0:
        agg_label = "positive"
    elif avg_score < 0:
        agg_label = "negative"
    else:
        agg_label = "neutral"

    return agg_label, avg_score

if __name__ == "__main__":
    rss_url = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"
    
    articles = scrape(rss_url)
    
    # Perform sentiment analysis on the scraped articles
    analyzed_articles = analyze_sentiment(articles)



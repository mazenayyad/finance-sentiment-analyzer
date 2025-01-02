from scripts.scraper import scrape
from transformers import BertTokenizer, BertForSequenceClassification
import torch

def analyze_sentiment(articles):
    # load finBERT
    tokenizer = BertTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    model = BertForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

    # analyze sentiment for each article
    for article in articles:
        title = article["title"]

        # preprocess the title
        inputs = tokenizer(title, return_tensors="pt", padding=True, truncation=True, max_length=512)

        # get predictions
        outputs = model(**inputs)
        logits = outputs.logits

        # convert logits to probabilities
        probabilities = torch.nn.functional.softmax(logits, dim=1)

        # get the predicted sentiment
        predicted_class = torch.argmax(probabilities, dim=1).item()

        # map the class to a sentiment label
        sentiment = ['negative', 'neutral', 'positive'][predicted_class]
        article["sentiment"] = sentiment # add sentiment to the article

    return articles

if __name__ == "__main__":
    rss_url = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"
    
    articles = scrape(rss_url)
    
    # Perform sentiment analysis on the scraped articles
    analyzed_articles = analyze_sentiment(articles)

    # Display the results
    print("Analyzed Articles:")
    for article in analyzed_articles:
        print(f"Title: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Published: {article['published']}")
        print(f"Sentiment: {article['sentiment']}")
        print(f"Link: {article['link']}")
        print("-" * 80)
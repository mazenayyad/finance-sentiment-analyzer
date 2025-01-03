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

        # tokenize the title for the model
        inputs = tokenizer(title, return_tensors="pt", padding=True, truncation=True, max_length=512)

        # send the tokenized title to the model
        outputs = model(**inputs)

        # extract logits from model (raw data)
        logits = outputs.logits

        # softmax to obtain human understandable probabilities
        probabilities = torch.nn.functional.softmax(logits, dim=1)

        # argmax to obtain the most likely class (negative neutral or positive)
        predicted_class = torch.argmax(probabilities, dim=1).item()

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
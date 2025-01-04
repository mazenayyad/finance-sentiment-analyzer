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

        # extract the 3 numbers
        p_neg, p_neu, p_pos = probabilities[0].tolist()

        # -100 to 100 sentiment score
        score = 100 * (p_pos - p_neg)

        article["sentiment_score"] = score # add sentiment score to the article

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


'''
probably dont force neutrality to be 0
however i want to have still a sentiment label like neutral positive or negative
such that if it was neutral, it wouldnt be 0, but close to 0. so user should know perhaps if that means
that its neutral or if its negative/positive? something to think about.
'''
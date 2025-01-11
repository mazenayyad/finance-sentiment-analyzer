from scripts.scraper import scrape
from transformers import BartTokenizer, BartForConditionalGeneration
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# loading a large model once is more efficient than for each function call
summarizer_tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
summarizer_model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")

# arg is articles which is a list of dictionaries of titles and content. so far its only doing title
def analyze_sentiment(articles):
    # load finBERT
    tokenizer = BertTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    model = BertForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

    # analyze sentiment for each article
    for article in articles:
        text_to_analyze = article["summary"]

        # tokenize the title for the model
        inputs = tokenizer(text_to_analyze, return_tensors="pt", padding=True, truncation=True, max_length=512)

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

def summarize_text(text):
    max_tokens = 1024
    max_summary_length = 150

    # tokenize the text
    inputs = summarizer_tokenizer.encode(text, return_tensors="pt", max_length=max_tokens, truncation=True)

    summary_ids = summarizer_model.generate(inputs, max_length=max_summary_length, min_length=30, num_beams=4, early_stopping=True)

    # takes the output tokens and converts them back into a string
    summary = summarizer_tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary

if __name__ == "__main__":
    rss_url = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"
    
    articles = scrape(rss_url)

    for article in articles:
        summary = summarize_text(article["content"])
        article["summary"] = summary
    
    # Perform sentiment analysis on the scraped articles
    analyzed_articles = analyze_sentiment(articles)

    agg_label, agg_score = aggregate_numeric_scores(analyzed_articles)

    print("Aggregate Sentiment Label:", agg_label)
    print("Aggregate Sentiment Score:", agg_score)
    
    for a in analyzed_articles:
        print("---")
        print("Title:", a["title"])
        print("URL:", a["final_url"])
        print("Summary:", a["summary"])
        print("Sentiment Score:", a["sentiment_score"])
        print("Sentiment Label:", a["sentiment_label"])
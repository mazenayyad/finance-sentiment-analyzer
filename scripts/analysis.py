import torch
from transformers import BartTokenizer, BartForConditionalGeneration
from transformers import BertTokenizer, BertForSequenceClassification

summarizer_tokenizer = None
summarizer_model = None
finbert_tokenizer = None
finbert_model = None

def init_models():
    global summarizer_tokenizer, summarizer_model
    global finbert_tokenizer, finbert_model

    # if models not initialized
    if summarizer_tokenizer is None or summarizer_model is None:
        summarizer_tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
        summarizer_model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    if finbert_tokenizer is None or finbert_model is None:
        finbert_tokenizer = BertTokenizer.from_pretrained("yiyanghkust/finbert-tone")
        finbert_model = BertForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

def summarize_text(text):
    if summarizer_tokenizer is None or summarizer_model is None:
        raise RuntimeError("BART models not loaded. Call init_models() first")
    
    max_tokens = 1024
    max_summary_length = 150

    # tokenize the text
    inputs = summarizer_tokenizer.encode(text, return_tensors="pt", max_length=max_tokens, truncation=True)

    # generate summary
    summary_ids = summarizer_model.generate(inputs, max_length=max_summary_length, min_length=30, num_beams=4, early_stopping=True)

    # takes the output tokens and converts them back into a string
    summary = summarizer_tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary


def analyze_sentiment(articles):
    if finbert_tokenizer is None or finbert_model is None:
        raise RuntimeError("FinBERT model not loaded. Call init_models() first")

    # analyze sentiment for each article
    for article in articles:
        text_to_analyze = article["summary"]

        # tokenize the title for the model
        inputs = finbert_tokenizer(text_to_analyze, return_tensors="pt", padding=True, truncation=True, max_length=512)

        # send the tokenized title to the model
        outputs = finbert_model(**inputs)

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

        sentiment = ['Neutral', 'Positive', 'Negative'][predicted_class]

        if sentiment == 'Neutral':
            if score > 15:
                sentiment = 'Positive'
            if score < -15:
                sentiment = 'Negative'
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

    rounded_score = int(round(avg_score))

    # decide overall label
    if rounded_score > 0:
        agg_label = "Positive"
    elif rounded_score < 0:
        agg_label = "Negative"
    else:
        agg_label = "Neutral"

    return agg_label, avg_score

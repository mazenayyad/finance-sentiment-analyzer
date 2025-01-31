# 1) Start from an official Python image (version 3.9 slim)
FROM python:3.9-slim

# 2) System-level dependencies
# Installing chromium & chromedriver for Selenium to work
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3) Creating a directory for the app inside the container
WORKDIR /app

# 4) Copy the requirements.txt, then install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copy the rest of the application code into the Docker image
COPY . .

# 6) Pre-download or cache hugging face models so it doesn't download each time the container is started
RUN python -c "from transformers import BartTokenizer, BartForConditionalGeneration; \
BartTokenizer.from_pretrained('facebook/bart-large-cnn'); \
BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn'); \
from transformers import BertTokenizer, BertForSequenceClassification; \
BertTokenizer.from_pretrained('yiyanghkust/finbert-tone'); \
BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-tone')"

# 7) Expose the port that Flask will run on
EXPOSE 5000

# Set env variable for ChromeDriver path
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"

# 8) Use Gunicorn to run the Flask app in production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers=1"]
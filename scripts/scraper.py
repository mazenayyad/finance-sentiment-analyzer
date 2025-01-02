import requests
from bs4 import BeautifulSoup
import time

def scrape_forbes_article(article_url):
    try:
        response = requests.get(article_url, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code != 200:
            return f"Failed to fetch forbes article. HTTP Status Code: {response.status_code}"

        html = response.content
        soup = BeautifulSoup(html, "html.parser") # parse raw HTML into a structured tree using Python's built-in HTML parser

        article_body = soup.find("div", class_="article-body fs-article fs-responsive-text current-article")
        if not article_body:
            return "Main content not found. The forbes page structure might have changed."
        
        paragraphs = article_body.find_all("p") # returns a list of all <p> tags

        paragraph_texts = []

        for p in paragraphs:
            text = p.get_text(strip=True)
            paragraph_texts.append(text)

        # join all the paragraph texts into one string, separated by spaces
        article_content = " ".join(paragraph_texts)

        return article_content

    except Exception as e:
        return f"An error occurred when fetching forbes article: {e}"

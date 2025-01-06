import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# load the environment variables from .env
load_dotenv()

def scrape(rss_url):
    response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code == 200:
        # parse from the rss feed
        root = ET.fromstring(response.content)
        # items = a list of all articles
        items = root.findall(".//item")

        articles = []

        for item in items:
            title = item.find("title").text
            redirect_link = item.find("link").text
            pub_date = item.find("pubDate").text
            source_name = item.find("source").text
            clean_title = title.split(" - ")[0]

            if 'forbes' in redirect_link.lower():
                content = forbes_scraper(get_final_url(redirect_link, 'forbes.com'))
                articles.append({
                "title": clean_title,
                "redirect_link": redirect_link,
                "published": pub_date,
                "source": source_name,
                "content": content
            })

        # will return the article content instead later
        return articles  # returns a list of articles with their metadata
    else:
        print(f"Failed to fetch RSS feed. HTTP Status Code: {response.status_code}")
        return []  # return an empty list in case of failure

def get_final_url(article_url, url_contains):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver_path = os.getenv("CHROMEDRIVER_PATH")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(article_url)
        WebDriverWait(driver, 10).until(EC.url_contains(f'{url_contains}'))
        final_url = driver.current_url
        return final_url
    finally:
        driver.quit()

def forbes_scraper(article_url):
    response = requests.get(article_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        article_div = soup.find('div', class_="article-body fs-article fs-responsive-text current-article")

        if article_div:
            paragraphs = article_div.find_all('p')
            content_lines = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                content_lines.append(text)
            content = " ".join(content_lines)
            return content
    else:
        return None
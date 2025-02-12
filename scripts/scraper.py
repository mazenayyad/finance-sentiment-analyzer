import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from database import article_exists
from datetime import datetime
import uuid
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# returns a list of articles. each article is a dictionary of title, final_url and content
def scrape(rss_url):
    response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code == 200:
        # parse xml from the rss feed
        root = ET.fromstring(response.content)
        # items = each article in the xml of rss feed
        items = root.findall('.//item')
        articles = []

        for item in items:
            title = item.find("title").text
            source_text = item.find("source").text
            clean_title = title.split(" - ")[0]
            pub_date = item.find("pubDate")
            pub_date_str = pub_date.text
            """
            parsed_pub_date is a string value of isoformat date, dt_utc is datetime
            dt_utc is datetime for comparison with datetime.utcnow().date()
            """
            parsed_pub_date, dt_utc = parse_pubdate(pub_date_str)
            if dt_utc.date() != datetime.utcnow().date():
                continue
            if article_exists(clean_title, source_text):
                continue
            redirect_link = item.find("link").text
            if 'forbes' in source_text.lower():
                url = get_final_url(redirect_link, "forbes.com")
                if url == "": # if there was an exception, go to the next 
                    continue

                content = forbes_scraper(url)
                article_dict = {
                    "title": clean_title,
                    "source": source_text,
                    "pub_date": parsed_pub_date,
                    "final_url": url,
                    "content": content
                }
                articles.append(article_dict)
            elif ('Yahoo Finance' == source_text):
                url = get_final_url(redirect_link, "finance.yahoo.com")
                if url == "":
                    continue
                if "uk.finance.yahoo.com" in url.lower():
                    continue

                content = yahoo_scraper(url)
                article_dict = {
                    "title": clean_title,
                    "source": source_text,
                    "pub_date": parsed_pub_date,
                    "final_url": url,
                    "content": content
                }
                articles.append(article_dict)
            elif ('Bitcoin.com News' == source_text):
                url = get_final_url(redirect_link, "news.bitcoin.com")
                if url == "":
                    continue
                
                content = news_bitcoin_com(url)
                article_dict = {
                    "title": clean_title,
                    "source": source_text,
                    "pub_date": parsed_pub_date,
                    "final_url": url,
                    "content": content
                }
                articles.append(article_dict)
            else:
                continue
        return articles
    else:
        print (f'Failed to fetch RSS feed. HTTP Status Code: {response.status_code}')
        return []
    

def parse_pubdate(pubdate):
    dt_utc = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S GMT") # convert to datetime object
    dt_utc_date = dt_utc.date() # strips off time, leaving only date
    return dt_utc_date.isoformat(), dt_utc

def get_final_url(redirect_url, contains):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # generate a unique directory for user data
    unique_dir = f"/tmp/chrome-{uuid.uuid4()}"
    chrome_options.add_argument(f'--user-data-dir={unique_dir}')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    final_url = "" # define early incase exception

    try:
        driver.get(redirect_url)
        WebDriverWait(driver, 10).until(EC.url_contains(contains.lower()))
        final_url = driver.current_url
    except Exception as e: # if we get here means WebDriverWait raised exception
        print(f'Redirect: {redirect_url}, Final: {final_url} Selenium Exception: {e}')
        return ""
    finally:
        driver.quit()

    return final_url

def yahoo_scraper(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        article_div = soup.find("div", class_=["body", "yf-tsvcyu"])

        if article_div:
            paragraphs = article_div.find_all("p", class_="yf-1pe5jgt")
            content_lines = []

            KEYWORDS = ["bitcoin", "crypto", "cryptocurrency", "btc", "ethereum", "eth"]
            for p in paragraphs:
                p_text = p.get_text(strip=True).lower()
                kw_found = False
                for kw in KEYWORDS:
                    if kw in p_text:
                        kw_found = True
                        break
                if not kw_found:
                    continue
                content_lines.append(p.get_text(strip=True))
            content = " ".join(content_lines)
            return content
        else:
            return ""
    else:
        return ""

def forbes_scraper(url):
    # return content which is a string
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        article_div = soup.find("div", class_=["article-body", "fs-article", "fs-responsive-text", "current-article"])

        if article_div:
            paragraphs = article_div.find_all("p")
            content_lines = []

            KEYWORDS = ["bitcoin", "crypto", "cryptocurrency", "btc", "ethereum", "eth"]
            for p in paragraphs:
                # if paragraph has a <strong> tag, skip it
                if p.find("strong") is not None:
                    continue
                # check if its a relevant paragraph
                p_text = p.get_text(strip=True).lower()
                kw_found = False
                for kw in KEYWORDS:
                    if kw in p_text:
                        kw_found = True
                        break # found at least 1 keyword. can stop checking
                if not kw_found:
                    continue

                # if passed both tests, keep it
                content_lines.append(p.get_text(strip=True))
            content = " ".join(content_lines)
            return content
        else:
            return ""
    else:
        return ""
    

def fetch_dynamic_url(url):
    """ 
    opens the given URL using Selenium, waits for the <div class="article__body"> to appear,
    then returns the entire HTML source as a string
    """

    # chrome options same as get_final_url
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # generate a unique user-data dir
    unique_dir = f"/tmp/chrome-{uuid.uuid4()}"
    chrome_options.add_argument(f'--user-data-dir={unique_dir}')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    page_source = ""

    try:
        driver.get(url)

        # wait for the div.article__body to appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.article__body"))
        )

        # once it’s present, grab the rendered page source
        page_source = driver.page_source

    except Exception as e:
        print(f"[fetch_dynamic_html] Exception: {e}")
        return ""

    finally:
        driver.quit()

    return page_source    
    
def news_bitcoin_com(url):
    rendered_html = fetch_dynamic_url(url)

    if not rendered_html:
        return ""

    # parse with bs4
    soup = BeautifulSoup(rendered_html, "html.parser")

    # find the div
    article_div = soup.find("div", class_="article__body")
    if not article_div:
        return ""

    paragraphs = article_div.find_all("p")
    content_lines = []
    KEYWORDS = ["bitcoin", "crypto", "cryptocurrency", "btc", "ethereum", "eth"]

    for p in paragraphs:
        p_text = p.get_text(strip=True).lower()
        kw_found = False
        for kw in KEYWORDS:
            if kw in p_text:
                kw_found = True
                break
        if not kw_found:
            continue

        content_lines.append(p.get_text(strip=True))

    # join into a single string
    content = " ".join(content_lines)
    return content

import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

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
            redirect_link = item.find("link").text
            clean_title = title.split(" - ")[0]
            source_text = item.find("source").text
            if 'forbes' in source_text.lower():
                url = get_final_url(redirect_link, "forbes.com")
                if url == "": # if there was an exception, go to the next 
                    continue
                
                content = forbes_scraper(url)
                article_dict = {
                    "title": clean_title,
                    "final_url": url,
                    "content": content
                }
                articles.append(article_dict)
            elif 'yahoo' in source_text.lower():
                url = get_final_url(redirect_link, "finance.yahoo.com")
                if url == "":
                    continue
                if "uk.finance.yahoo.com" in url.lower():
                    continue

                content = yahoo_scraper(url)
                article_dict = {
                    "title": clean_title,
                    "final_url": url,
                    "content": content
                }
            else:
                continue
        return articles
    else:
        print (f'Failed to fetch RSS feed. HTTP Status Code: {response.status_code}')
        return []
    
def get_final_url(redirect_url, contains):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver_path = os.getenv("CHROMEDRIVER_PATH")
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(redirect_url)
        WebDriverWait(driver, 10).until(EC.url_contains(contains.lower()))
        final_url = driver.current_url
    except Exception as e: # if we get here means WebDriverWait raised exception
        print(f'{redirect_url} Selenium Exception: {e}')
        return ""
    finally:
        driver.quit()

    return final_url

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
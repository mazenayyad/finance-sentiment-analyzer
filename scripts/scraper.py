import requests
import xml.etree.ElementTree as ET

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
            link = item.find("link").text
            pub_date = item.find("pubDate").text
            source_name = item.find("source").text
            clean_title = title.split(" - ")[0]
            articles.append({
                "title": clean_title,
                "link": link,
                "published": pub_date,
                "source": source_name
            })
        return articles  # returns a list of articles with their metadata
    else:
        print(f"Failed to fetch RSS feed. HTTP Status Code: {response.status_code}")
        return []  # return an empty list in case of failure

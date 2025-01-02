import requests
import xml.etree.ElementTree as ET

# RSS feed URL for Bitcoin news
rss_url = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"

# Fetch the RSS feed
response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})

# Parse the XML content
root = ET.fromstring(response.content)

# Extract and display articles
for item in root.findall(".//item"):
    title = item.find("title").text
    link = item.find("link").text
    pub_date = item.find("pubDate").text

    print(f"Title: {title}")
    print(f"Link: {link}")
    print(f"Published: {pub_date}")
    print("-" * 40)

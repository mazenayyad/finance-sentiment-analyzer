import requests
import xml.etree.ElementTree as ET

rss_url = "https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en"
response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})

if response.status_code == 200:
    # parse the rss feed
    root = ET.fromstring(response.content)

    # list of all articles
    items = root.findall(".//item")

    forbes_content = []

    for item in items:
        title = item.find("title").text
        link = item.find("link").text
        pub_date = item.find("pubDate").text

        source_tag = item.find("source")
        if source_tag is not None:
            source_url = source_tag.get("url")
            source_name = source_tag.text

            if "forbes.com" in source_url:
                forbes_content.append({
                    "title": title,
                    "source": source_name,
                    "source_url": source_url,
                    "redirect_link": link, # google news redirect link
                    "published": pub_date
                })

else:
    print(f"Failed to fetch RSS feed. HTTP Status Code: {response.status_code}")
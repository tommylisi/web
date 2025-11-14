import re
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from dateutil import parser
from datetime import datetime
import pytz

URL = "https://lancasteronline.com/staff/tomlisi/"

def fetch_articles():
    """Scrapes articles and extracts relevant details."""
    response = requests.get(URL)
    if response.status_code != 200:
        print("Failed to retrieve page")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # CORRECTED SELECTOR: Target the parent element containing article details
    # The articles are within a simple .tnt-asset class on this page
    for article in soup.select("article.tnt-asset"):
        
        # --- TITLE and LINK ---
        title_tag = article.select_one(".tnt-headline a")
        link_tag = article.select_one(".tnt-headline a")
        
        link = link_tag["href"] if link_tag else None
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # Ensure full URL for links
        if link and not link.startswith("http"):
            link = "https://lancasteronline.com" + link

        # --- DESCRIPTION ---
        summary_tag = article.select_one(".tnt-summary")
        description = summary_tag.get_text(strip=True) if summary_tag else ""

        # --- PUBLICATION DATE ---
        date_tag = article.select_one("time")
        pub_date = None
        if date_tag and "datetime" in date_tag.attrs:
            try:
                # The datetime attribute is often ISO 8601, parse it, and then localize/format
                dt_obj = parser.parse(date_tag["datetime"])
                # Assume ET timezone (Lancaster, PA) if not specified
                if dt_obj.tzinfo is None or dt_obj.tzinfo.utcoffset(dt_obj) is None:
                    est = pytz.timezone('America/New_York')
                    dt_obj = est.localize(dt_obj)
                
                # Format for RSS
                pub_date = dt_obj.strftime("%a, %d %b %Y %H:%M:%S %z")
            except Exception as e:
                print(f"Invalid date format: {date_tag['datetime']} - Error: {e}")

        # --- IMAGE ---
        # Look for the image tag within the article
        image_url = []
        image_tag = article.select_one(".tnt-image img")
        
        if image_tag and "data-srcset" in image_tag.attrs:
            srcset = image_tag["data-srcset"]
            
            # Simplified regex: find the last (largest) valid URL in the srcset
            # This is often the best practice unless you specifically need small sizes
            matches = re.findall(r'(https://[^\s,]+)', srcset)
            
            # Get the URL associated with the highest resolution/width (usually the last match)
            if matches:
                image_url.append(matches[-1]) 
            
        
        articles.append({
            "title": title,
            "link": link,
            "description": description,
            "image": image_url[0] if image_url else None, # Pass a single URL or None
            "pub_date": pub_date
        })

    return articles

def generate_rss(articles):
    """Generates an RSS feed."""
    fg = FeedGenerator()
    fg.title("Tom Lisi's Articles - LancasterOnline")
    fg.link(href=URL, rel="self")
    fg.description("Latest articles from journalist Tom Lisi on LancasterOnline")
    fg.language('en') # Best practice to set a language

    for article in articles:
        fe = fg.add_entry()
        fe.title(article["title"])
        fe.link(href=article["link"])
        fe.description(article["description"])
        
        if article["pub_date"]:
            try:
                # pubDate expects a properly formatted string, which you've created
                fe.pubDate(article["pub_date"])
            except Exception as e:
                print(f"Error setting pubDate for {article['title']}: {e}")
        
        # Only add enclosure if an image URL was successfully found
        if article["image"]:
            # NOTE: We assume 'image/jpeg' and size=0 as a placeholder, 
            # as file size isn't easily known from srcset.
            fe.enclosure(article["image"], 0, "image/jpeg") 

    return fg.rss_str(pretty=True)

def save_rss_feed():
    """Fetches articles and saves the RSS feed."""
    articles = fetch_articles()
    if not articles:
        print("No articles found. Check selector or URL.")
        return

    rss_feed = generate_rss(articles)

    with open("tom_lisi_feed.xml", "wb") as f:
        f.write(rss_feed)
    
    print("RSS feed saved as tom_lisi_feed.xml")

if __name__ == "__main__":
    save_rss_feed()
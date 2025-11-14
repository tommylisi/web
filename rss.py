import requests
import feedgen.feed
from dateutil import parser
import pytz
import json
import re
import time 
import random # <--- ESSENTIAL: Added for 429 Error Fix

URL = "https://lancasteronline.com/staff/tomlisi/"
JSON_API_URL = "https://lancasteronline.com/search/?l=20&a=Tom%20Lisi&f=json"
# <--- ESSENTIAL: Added for 429 Error Fix
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://lancasteronline.com/staff/tomlisi/',
}

def fetch_articles():
    """Fetches articles directly from the site's JSON API endpoint with headers and retry logic."""
    
    max_retries = 3
    for attempt in range(max_retries):
        print(f"Requesting JSON data from: {JSON_API_URL} (Attempt {attempt + 1}/{max_retries})")
        
        # 1. Request the JSON API URL with HEADERS
        response = requests.get(JSON_API_URL, headers=HEADERS) # <--- ESSENTIAL: Use HEADERS
        
        if response.status_code == 200:
            # Success! Proceed to parse
            try:
                data = response.json()
            except json.JSONDecodeError:
                print("Failed to decode JSON response.")
                return []

            articles = []
            results = data.get('results', [])
            
            if not results:
                print("JSON API returned no article results.")
                return []

            # 2. Loop through the JSON results (Your parsing logic)
            for item in results:
                title = item.get('title')
                link = item.get('url')
                description = item.get('summary', '')
                date_string = item.get('display_time', item.get('publish_time'))
                
                if link and not link.startswith("http"):
                    link = "https://lancasteronline.com" + link

                pub_date = None
                if date_string:
                    try:
                        dt_obj = parser.parse(date_string)
                        if dt_obj.tzinfo is None or dt_obj.tzinfo.utcoffset(dt_obj) is None:
                            est = pytz.timezone('America/New_York')
                            dt_obj = est.localize(dt_obj).astimezone(pytz.utc) 
                        pub_date = dt_obj.strftime("%a, %d %b %Y %H:%M:%S +0000")
                    except Exception as e:
                        print(f"Invalid date format in JSON: {date_string} - Error: {e}")

                image_url = None
                primary_image = item.get('image', {})
                if primary_image:
                    image_url = primary_image.get('url')
                
                if not all([title, link]):
                    continue
                    
                articles.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "image": image_url,
                    "pub_date": pub_date
                })
                
            return articles
            
        elif response.status_code == 429:
            # Hit the rate limit. Wait and retry.
            print(f"Received 429: Too Many Requests. Waiting before retry...")
            wait_time = random.uniform(3, 7) # <--- ESSENTIAL: Random delay
            time.sleep(wait_time)
            
        else:
            print(f"Failed to retrieve API data, status code: {response.status_code}")
            return []
            
    # If all retries fail
    print(f"Failed to retrieve data after {max_retries} attempts.")
    return []

# --- Main function to generate the RSS feed (No changes needed below here) ---

def generate_rss_feed(articles):
    """Generates the RSS feed XML."""
    fg = feedgen.feed.FeedGenerator()
    fg.title('Tom Lisi - LancasterOnline')
    fg.link(href=URL, rel='alternate')
    fg.description('Latest articles written by Tom Lisi for LNP|LancasterOnline.')

    for article in articles:
        fe = fg.add_entry()
        fe.id(article['link'])
        fe.link(href=article['link'])
        fe.title(article['title'])
        
        content = article['description']
        if article['image']:
            content = f"<![CDATA[<img src=\"{article['image']}\" />{content}]]>"
        
        fe.description(content)
        
        if article['pub_date']:
            fe.pubDate(article['pub_date']) 

    return fg.rss_str(pretty=True)

# Main execution block
if __name__ == "__main__":
    articles_data = fetch_articles()
    
    if articles_data:
        rss_output = generate_rss_feed(articles_data)
        print("\n--- RSS Feed Generated Successfully (Partial Output) ---")
        print(rss_output[:1000].decode('utf-8'))
    else:
        print("\nCould not generate RSS feed. No articles were successfully extracted.")
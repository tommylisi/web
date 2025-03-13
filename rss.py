import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from dateutil import parser

URL = "https://lancasteronline.com/staff/tomlisi/"

def fetch_articles():
    """Scrapes articles and extracts relevant details."""
    response = requests.get(URL)
    if response.status_code != 200:
        print("Failed to retrieve page")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for article in soup.select("article.tnt-asset-type-article"):
        title_tag = article.select_one(".tnt-headline")
        link_tag = article.select_one(".image a")
        link = link_tag["href"] if link_tag else None
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        summary_tag = article.select_one("p.tnt-summary")
        description = summary_tag.get_text(strip=True) if summary_tag else ""

        # Extract the largest image from data-srcset
        image_tag = article.select_one("div.img")
        image_url = None
        if image_tag:
            if "data-srcset" in image_tag.attrs:
                srcset = image_tag["data-srcset"].split(", ")
                largest_image = srcset[-1].split(" ")[0]  # Last entry in srcset should be the largest
                image_url = largest_image
            elif "src" in image_tag.attrs:
                image_url = image_tag["src"]  # Fallback to `src`


        # Ensure full URL for links
        if link and not link.startswith("http"):
            link = "https://lancasteronline.com" + link  

        # Extract and validate date
        date_tag = article.select_one("time")
        pub_date = None
        if date_tag and "datetime" in date_tag.attrs:
            try:
                pub_date = parser.parse(date_tag["datetime"]).strftime("%a, %d %b %Y %H:%M:%S %z")
            except Exception as e:
                print(f"Invalid date format: {date_tag['datetime']} - Error: {e}")


        articles.append({
            "title": title,
            "link": link,
            "description": description,
            "image": image_url,
            "pub_date": pub_date
        })
    return list(reversed(articles))
def generate_rss(articles):
    """Generates an RSS feed."""
    fg = FeedGenerator()
    fg.title("Tom Lisi's Articles - LancasterOnline")
    fg.link(href=URL, rel="self")
    fg.description("Latest articles from journalist Tom Lisi on LancasterOnline")

    for article in articles:
        fe = fg.add_entry()
        fe.title(article["title"])
        fe.link(href=article["link"])
        fe.description(article["description"])
        if article["pub_date"]:
            try:
                fe.pubDate(article["pub_date"])
            except Exception as e:
                print(f"Error setting pubDate for {article['title']}: {e}")
        fe.enclosure(article["image"], 0, "image/jpeg")  # Adding large image

    return fg.rss_str(pretty=True)

def save_rss_feed():
    """Fetches articles and saves the RSS feed."""
    articles = fetch_articles()
    if not articles:
        print("No articles found.")
        return

    rss_feed = generate_rss(articles)

    with open("tom_lisi_feed.xml", "wb") as f:
        f.write(rss_feed)
    
    print("RSS feed saved as tom_lisi_feed.xml")

if __name__ == "__main__":
    save_rss_feed()

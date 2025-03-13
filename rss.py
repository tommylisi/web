import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# URL of Tom Lisi's articles page
URL = "https://lancasteronline.com/staff/tomlisi/"

def fetch_articles():
    """Scrape Tom Lisi's latest articles from LancasterOnline."""
    response = requests.get(URL)
    if response.status_code != 200:
        print("Failed to fetch the page.")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []

    # Find article elements
    for article in soup.select("article.tnt-asset-type-article"):
        title_tag = article.select_one("h3.tnt-headline a")
        link = title_tag["href"] if title_tag else None
        full_link = f"https://lancasteronline.com{link}" if link else None

        date_tag = article.select_one("time")
        pub_date = date_tag["datetime"] if date_tag else None

        summary_tag = article.select_one("p.tnt-summary")
        summary = summary_tag.text.strip() if summary_tag else "No summary available."

        # Get the image URL (largest one)
        image_tag = article.select_one("img.img-responsive")
        if image_tag:
            image_srcset = image_tag.get("data-srcset", "").split(", ")
            if image_srcset:
                # Get the last (largest) image in the srcset
                largest_image_url = image_srcset[-1].split(" ")[0]
            else:
                largest_image_url = image_tag.get("src")  # Fallback to standard src
        else:
            largest_image_url = None

        # Store article data, including the largest image
        if title_tag and full_link and pub_date:
            articles.append({
                "title": title_tag.text.strip(),
                "link": full_link,
                "pub_date": pub_date,
                "summary": summary,
                "image": largest_image_url  # Using the largest image URL
            })

    return articles

def generate_rss(articles):
    """Generate an RSS feed from scraped articles."""
    fg = FeedGenerator()
    fg.title("Tom Lisi - LancasterOnline RSS")
    fg.link(href=URL, rel="self")
    fg.description("Latest articles by Tom Lisi from LancasterOnline")

    for article in articles:
        fe = fg.add_entry()
        fe.title(article["title"])
        fe.link(href=article["link"])
        fe.published(article["pub_date"])
        fe.description(article["summary"])

        # Add the image URL to the RSS feed entry
        if article["image"]:
            fe.enclosure(article["image"], 0, "image/jpeg")  # Add image to RSS feed

    # Save the RSS feed
    with open("tom_lisi_feed.xml", "wb") as f:
        f.write(fg.rss_str(pretty=True))

    print("RSS feed generated: tom_lisi_feed.xml")

if __name__ == "__main__":
    articles = fetch_articles()
    if articles:
        generate_rss(articles)
    else:
        print("No articles found.")

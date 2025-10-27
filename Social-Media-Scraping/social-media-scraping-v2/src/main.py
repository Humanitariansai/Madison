# src/main.py
from scrapers.twitter_scraper import TwitterScraper
from scrapers.reddit_scraper import RedditScraper
from storage.db import DataStore
import os
from dotenv import load_dotenv

load_dotenv()

def scrape_and_store(keyword: str):
    """Scrape from all platforms and store"""
    store = DataStore()
    
    # Twitter
    print(f"Scraping Twitter for '{keyword}'...")
    twitter = TwitterScraper()
    tweets = twitter.search_tweets(keyword, max_results=50)
    for tweet in tweets:
        post = {
            "id": tweet["id"],
            "platform": "twitter",
            "title": tweet.get("text", "")[:100],
            "content": tweet.get("text", ""),
            "author": tweet.get("author_id"),
            "url": f"https://twitter.com/i/web/status/{tweet['id']}",
            "metrics": tweet.get("public_metrics", {}),
            "created_at": tweet.get("created_at")
        }
        stored = store.insert_post(post)
        print(f"  Stored: {stored}")
    
    # Reddit
    print(f"Scraping Reddit for '{keyword}'...")
    reddit = RedditScraper()
    posts = reddit.search_subreddits(keyword, limit=50)
    for post in posts:
        stored_post = {
            "id": post["id"],
            "platform": "reddit",
            "title": post.get("title"),
            "content": post.get("text"),
            "author": post.get("author"),
            "url": post.get("url"),
            "metrics": {"score": post["score"], "comments": post["comments"]},
            "created_at": post.get("created_at")
        }
        stored = store.insert_post(stored_post)
        print(f"  Stored: {stored}")

if __name__ == "__main__":
    scrape_and_store("Apple")
    print("Scraping complete!")
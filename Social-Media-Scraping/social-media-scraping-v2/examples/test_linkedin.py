#!/usr/bin/env python3
from src.scrapers.linkedin_scraper import LinkedInScraper

# Initialize scraper
scraper = LinkedInScraper(headless=True)

try:
    # Search for brand-related posts
    posts = scraper.search_posts("artificial intelligence", limit=5)
    
    # Display results
    for post in posts:
        print("\n--- Post ---")
        print(f"Author: {post['author']}")
        print(f"Content: {post['content'][:200]}...")  # First 200 chars
        print(f"Engagement: {post['engagement']}")
        print(f"URL: {post['url']}")
        print("-----------")
finally:
    scraper.close()
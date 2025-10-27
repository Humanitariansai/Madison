#!/usr/bin/env python3
"""
Usage examples for the Social Media Scraping tool
Run this file to see common usage patterns
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.reddit_scraper import RedditScraper
from scrapers.twitter_scraper import TwitterScraper
from storage.db import DataStore

def example_1_basic_reddit_scraping():
    """Example 1: Basic Reddit scraping"""
    print("📱 Example 1: Basic Reddit Scraping")
    print("-" * 40)
    
    scraper = RedditScraper()
    posts = scraper.search_subreddits("artificial intelligence", limit=5)
    
    print(f"Found {len(posts)} posts about AI:")
    for i, post in enumerate(posts, 1):
        print(f"{i}. r/{post['subreddit']}: {post['title'][:60]}...")
        print(f"   Score: {post['score']}, Comments: {post['comments']}")
    print()

def example_2_specific_subreddit():
    """Example 2: Get posts from specific subreddit"""
    print("🐍 Example 2: Python Subreddit Posts")
    print("-" * 40)
    
    scraper = RedditScraper()
    posts = scraper.get_subreddit_posts("python", limit=3)
    
    print(f"Latest posts from r/python:")
    for i, post in enumerate(posts, 1):
        print(f"{i}. {post['title'][:60]}...")
        print(f"   Score: {post['score']}, Comments: {post['comments']}")
    print()

def example_3_database_operations():
    """Example 3: Database storage and queries"""
    print("💾 Example 3: Database Operations")
    print("-" * 40)
    
    store = DataStore()
    
    # Insert sample post
    sample_post = {
        "id": f"demo_{datetime.now().timestamp()}",
        "platform": "demo",
        "title": "Demo Post for Documentation",
        "content": "This is a sample post to demonstrate database functionality",
        "author": "demo_user",
        "url": "https://example.com/demo",
        "metrics": {"score": 42, "likes": 15},
        "created_at": datetime.now()
    }
    
    success = store.insert_post(sample_post)
    print(f"Inserted demo post: {success}")
    
    # Search posts
    results = store.search_posts("demo", limit=5)
    print(f"Found {len(results)} posts containing 'demo'")
    
    # Get stats
    stats = store.get_stats()
    print(f"Database stats: {stats}")
    print()

def example_4_full_workflow():
    """Example 4: Complete scraping and storage workflow"""
    print("🔄 Example 4: Complete Workflow")
    print("-" * 40)
    
    # Initialize components
    reddit = RedditScraper()
    store = DataStore()
    
    # Scrape data
    print("Scraping Reddit posts about 'machine learning'...")
    posts = reddit.search_subreddits("machine learning", limit=3)
    
    # Store data
    stored_count = 0
    for post in posts:
        post_data = {
            "id": post["id"],
            "platform": "reddit",
            "title": post["title"],
            "content": post["text"],
            "author": post["author"],
            "url": post["url"],
            "metrics": {"score": post["score"], "comments": post["comments"]},
            "created_at": post["created_at"]
        }
        
        if store.insert_post(post_data):
            stored_count += 1
            print(f"  ✅ Stored: {post['title'][:50]}...")
        else:
            print(f"  ⚠️  Duplicate: {post['title'][:50]}...")
    
    print(f"\nStored {stored_count} new posts")
    print()

def example_5_data_export():
    """Example 5: Export data to different formats"""
    print("📤 Example 5: Data Export")
    print("-" * 40)
    
    store = DataStore()
    
    # Get recent posts
    posts = store.filter_by_platform("reddit", limit=5)
    
    # Export to CSV-like format
    print("Sample data export (CSV format):")
    print("ID,Platform,Title,Score,Date")
    print("-" * 60)
    
    for post in posts:
        title = post.get('title', 'No title')[:30].replace(',', ';')
        score = post.get('engagement_metrics', {}).get('score', 0)
        date = post.get('created_at', 'Unknown')
        print(f"{post['id']},reddit,{title},{score},{date}")
    
    print()

if __name__ == "__main__":
    print("🚀 Social Media Scraping - Usage Examples")
    print("=" * 50)
    print()
    
    try:
        example_1_basic_reddit_scraping()
        example_2_specific_subreddit()
        example_3_database_operations()
        example_4_full_workflow()
        example_5_data_export()
        
        print("✅ All examples completed successfully!")
        print("\n💡 Tips:")
        print("- Check your .env file for API credentials")
        print("- Twitter may be rate-limited, focus on Reddit for now")
        print("- Run 'python tests/test_scrapers.py' to test your setup")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check your .env file has all required credentials")
        print("3. Test API connections: python test_apis.py")
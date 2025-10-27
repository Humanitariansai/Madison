#!/usr/bin/env python3
"""
Basic tests for social media scrapers
"""
import sys
import os
import unittest
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.reddit_scraper import RedditScraper
from scrapers.twitter_scraper import TwitterScraper
from storage.db import DataStore

class TestRedditScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = RedditScraper()
    
    def test_search_subreddits(self):
        """Test Reddit search functionality"""
        posts = self.scraper.search_subreddits("test", limit=2)
        self.assertIsInstance(posts, list)
        
        if posts:  # If we got results
            post = posts[0]
            required_fields = ['id', 'title', 'subreddit', 'score', 'created_at']
            for field in required_fields:
                self.assertIn(field, post)
    
    def test_get_subreddit_posts(self):
        """Test getting posts from specific subreddit"""
        posts = self.scraper.get_subreddit_posts("test", limit=2)
        self.assertIsInstance(posts, list)

class TestTwitterScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = TwitterScraper()
    
    def test_search_tweets(self):
        """Test Twitter search (may fail due to rate limits/access)"""
        # This test might fail due to API limitations
        tweets = self.scraper.search_tweets("hello", max_results=2)
        self.assertIsInstance(tweets, list)

class TestDataStore(unittest.TestCase):
    def setUp(self):
        self.store = DataStore()
    
    def test_insert_post(self):
        """Test inserting a post"""
        test_post = {
            'id': f'test_{datetime.now().timestamp()}',
            'platform': 'test',
            'title': 'Test Post',
            'content': 'Test content',
            'author': 'test_user',
            'url': 'https://test.com',
            'metrics': {'score': 1},
            'created_at': datetime.now()
        }
        
        result = self.store.insert_post(test_post)
        self.assertTrue(result)
        
        # Test duplicate detection
        duplicate_result = self.store.insert_post(test_post)
        self.assertFalse(duplicate_result)
    
    def test_search_posts(self):
        """Test searching posts"""
        results = self.store.search_posts("test", limit=5)
        self.assertIsInstance(results, list)
    
    def test_get_stats(self):
        """Test getting database stats"""
        stats = self.store.get_stats()
        self.assertIn('total_posts', stats)
        self.assertIn('platforms', stats)

if __name__ == '__main__':
    print("🧪 Running social media scraper tests...")
    unittest.main(verbosity=2)
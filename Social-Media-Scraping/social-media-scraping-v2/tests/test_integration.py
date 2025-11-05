#!/usr/bin/env python3
"""
Integration Tests for Social Media Scraping System
Tests the interaction between different components of the system
"""

import unittest
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.reddit_scraper import RedditScraper
from storage.db import DataStore
from utils.rate_limiter import RateLimiter, rate_limiter

class TestDataProcessingPipeline(unittest.TestCase):
    """Test the complete data processing pipeline"""
    
    def print_db_stats(self, prefix=""):
        """Print database statistics"""
        stats = self.store.get_stats()
        print(f"\n{prefix} Database stats:")
        print(f"Total posts: {stats['total_posts']}")
        print(f"Platforms: {stats['platforms']}")
        for platform_stat in stats['by_platform']:
            print(f"- {platform_stat['platform']}: {platform_stat['count']} posts")
    
    def setUp(self):
        """Initialize components for testing"""
        self.reddit = RedditScraper()
        self.store = DataStore()
        # List to track IDs of posts added during tests
        self.test_post_ids = []
        
        # Print stats before test
        self.print_db_stats("BEFORE TEST")
        
    def tearDown(self):
        """Clean up after each test"""
        # Print stats before cleanup
        self.print_db_stats("BEFORE TEARDOWN")
        
        # Clean up test posts using both ID tracking and is_test_data flag
        print("\nCleaning up test posts...")
        
        # Query to find test posts either by ID or by test flag
        query = {
            "$or": [
                # Posts we tracked by ID
                {"id": {"$in": self.test_post_ids}} if self.test_post_ids else {},
                # All posts marked as test data
                {"is_test_data": True}
            ]
        }
        
        result = self.store.db.posts.delete_many(query)
        print(f"Deleted {result.deleted_count} test posts")
        
        # Print stats after cleanup
        self.print_db_stats("AFTER TEARDOWN")
        
        # Close the database connection
        self.store.client.close()
        
    def test_data_deduplication(self):
        """Test that duplicate posts are properly handled"""
        # Create a test post with a unique test identifier
        test_post = {
            "id": f"test123_{datetime.now().timestamp()}",
            "platform": "reddit",
            "title": "Test Post",
            "content": "Test Content",
            "author": "test_author",
            "created_at": datetime.now(),
            "is_test_data": True  # Mark as test data
        }
        
        # Track this test post
        self.test_post_ids.append(test_post["id"])
        
        # First insertion should succeed
        result1 = self.store.insert_post(test_post)
        self.assertTrue(result1)
        
        # Second insertion of same post should fail/skip
        result2 = self.store.insert_post(test_post)
        self.assertFalse(result2)

    def test_search_and_filter(self):
        """Test search and filter functionality with real data"""
        # Insert test posts with unique test identifiers
        timestamp = datetime.now().timestamp()
        test_post = {
            "id": f"test_r1_{timestamp}",
            "platform": "reddit",
            "title": "Python Tutorial",
            "content": "Python for beginners",
            "created_at": datetime.now(),
            "is_test_data": True
        }
        
        self.test_post_ids.append(test_post["id"])
        self.store.insert_post(test_post)
            
        # Test search
        results = self.store.search_posts("Python")
        self.assertGreaterEqual(len(results), 1)
        
        # Test platform filter
        reddit_posts = self.store.filter_by_platform("reddit")
        self.assertGreaterEqual(len(reddit_posts), 1)
        self.assertEqual(reddit_posts[0]["platform"], "reddit")

class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.rate_limiter = RateLimiter()
    
    def test_rate_limiting_timing(self):
        """Test that rate limiting properly delays requests"""
        platform = "twitter"
        start_time = datetime.now()
        
        # Make multiple requests
        for _ in range(3):
            self.rate_limiter.wait_if_needed(platform)
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        # Should have waited at least 2 seconds (1s * 2 intervals)
        self.assertGreaterEqual(elapsed, 2.0)

class TestRedditIntegration(unittest.TestCase):
    """Integration tests for Reddit scraping functionality"""
    
    def print_db_stats(self, prefix=""):
        """Print database statistics"""
        stats = self.store.get_stats()
        print(f"\n{prefix} Database stats:")
        print(f"Total posts: {stats['total_posts']}")
        print(f"Platforms: {stats['platforms']}")
        for platform_stat in stats['by_platform']:
            print(f"- {platform_stat['platform']}: {platform_stat['count']} posts")
    
    def setUp(self):
        """Initialize components for testing"""
        self.reddit = RedditScraper()
        self.store = DataStore()
        # List to track IDs of posts added during tests
        self.test_post_ids = []
        
        # Print stats before test
        self.print_db_stats("BEFORE TEST")
        
    def tearDown(self):
        """Clean up after each test"""
        # Print stats before cleanup
        self.print_db_stats("BEFORE TEARDOWN")
        
        # Clean up test posts using both ID tracking and is_test_data flag
        print("\nCleaning up test posts...")
        
        # Query to find test posts either by ID or by test flag
        query = {
            "$or": [
                # Posts we tracked by ID
                {"id": {"$in": self.test_post_ids}} if self.test_post_ids else {},
                # All posts marked as test data
                {"is_test_data": True}
            ]
        }
        
        result = self.store.db.posts.delete_many(query)
        print(f"Deleted {result.deleted_count} test posts")
        
        # Print stats after cleanup
        self.print_db_stats("AFTER TEARDOWN")
        
        # Close the database connection
        self.store.client.close()
    
    def test_scrape_and_store(self):
        """Test the complete flow from scraping to storage"""
        # Test keyword
        keyword = "python programming"
        test_run_id = f"test_run_{datetime.now().timestamp()}"  # Unique identifier for this test run
        
        # Scrape from Reddit
        reddit_posts = self.reddit.search_subreddits(keyword, limit=5)
        self.assertIsInstance(reddit_posts, list)
        print(f"\nDebug - Number of Reddit posts found: {len(reddit_posts)}")
        
        if reddit_posts:
            # Store first Reddit post
            post = reddit_posts[0]
            print(f"Debug - First post data: {post.get('id')}, {post.get('title')}")
            
            # Create test post with unique identifier
            post_data = {
                "id": f"test_{post['id']}_{test_run_id}",  # Unique test ID
                "platform": "reddit",
                "title": post["title"],
                "content": post["text"],
                "author": post["author"],
                "created_at": post["created_at"],
                "is_test_data": True,
                "test_run_id": test_run_id  # Add test run identifier
            }
            
            # Track the test post
            self.test_post_ids.append(post_data["id"])
            
            print(f"Debug - Storing post with data: {post_data}")
            stored = self.store.insert_post(post_data)
            self.assertTrue(stored)
            print(f"Debug - Insert successful: {stored}")
            
            # Verify retrieval by searching for a word we know is in the title
            search_term = post["title"].split()[0]  # Use the first word from the title
            print(f"Debug - Searching for term from title: '{search_term}'")
            results = self.store.search_posts(search_term)
            print(f"Debug - Search results for '{search_term}': {len(results)}")
            self.assertGreaterEqual(len(results), 1)
            
    def test_reddit_search(self):
        """Test Reddit platform search functionality"""
        # Use a very common search term that's likely to get results
        keyword = "python"  # Changed from "technology" as it's more specific and common
        test_run_id = f"test_run_{datetime.now().timestamp()}"
        
        # Get posts from Reddit
        print(f"\nSearching Reddit for '{keyword}'...")
        reddit_posts = self.reddit.search_subreddits(keyword, limit=5)  # Increased limit
        
        if not reddit_posts:
            self.skipTest("No Reddit posts found - network or API issue")
        
        print(f"Found {len(reddit_posts)} posts from Reddit")
        
        # Store Reddit posts and track which should be searchable
        posts_with_keyword = []
        for post in reddit_posts:
            # Create test post
            post_data = {
                "id": f"test_reddit_{post['id']}_{test_run_id}",
                "platform": "reddit",
                "title": post["title"],
                "content": post["text"],
                "created_at": post["created_at"],
                "is_test_data": True,
                "test_run_id": test_run_id
            }
            
            # Track if this post should be findable by search
            if keyword.lower() in post["title"].lower() or (post["text"] and keyword.lower() in post["text"].lower()):
                posts_with_keyword.append(post_data["id"])
                print(f"Post should be searchable - Title: {post['title']}")
            
            self.test_post_ids.append(post_data["id"])
            success = self.store.insert_post(post_data)
            print(f"Post insert success: {success}")
            
            # Debug: Try to find the post we just inserted
            stored_post = self.store.db.posts.find_one({"id": post_data["id"]})
            if stored_post:
                print(f"Found stored post: id={stored_post.get('id')}, title={stored_post.get('title')}")
            else:
                print(f"Failed to find post with id {post_data['id']}")
        
        if not posts_with_keyword:
            self.skipTest("No posts contained the search keyword in title or content")
            
        # Search for posts
        print(f"\nSearching stored posts for '{keyword}'...")
        
        # Debug: Show what's in the database first
        all_results = list(self.store.db.posts.find())
        print(f"\nAll posts in database ({len(all_results)}):")
        for post in all_results:
            print(f"Post: title='{post.get('title')}', is_test_data={post.get('is_test_data')}")

        # Try the regular search
        results = self.store.search_posts(keyword)
        test_posts = [post for post in results if post.get("is_test_data")]
        print(f"Found {len(test_posts)} test posts in search results")
        
        # Should have found test posts
        self.assertGreaterEqual(len(test_posts), 1, 
            f"Expected to find posts with keyword '{keyword}', but found none. "
            f"There were {len(posts_with_keyword)} posts that should have matched.")
            
        # All found posts should be from Reddit
        self.assertTrue(all(post["platform"] == "reddit" for post in test_posts))

if __name__ == '__main__':
    unittest.main()
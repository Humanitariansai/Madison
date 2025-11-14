#!/usr/bin/env python3
"""
Performance Benchmarking Tool

This script measures and reports performance metrics for:
- Reddit scraping speed
- LinkedIn scraping speed
- Database insertion speed
- Memory usage
"""

import sys
import time
from pathlib import Path
import psutil
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.reddit_scraper import RedditScraper
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.storage.db import DataStore

class PerformanceBenchmark:
    """Performance benchmarking utility"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.results = {}
    
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def benchmark_reddit_scraping(self, query="Python", limit=20):
        """Benchmark Reddit scraping performance"""
        print(f"\n🔍 Benchmarking Reddit scraping ({limit} posts)...")
        print("=" * 60)
        
        mem_before = self.get_memory_usage()
        start_time = time.time()
        
        try:
            scraper = RedditScraper()
            posts = scraper.search_subreddits(query=query, limit=limit)
            
            end_time = time.time()
            mem_after = self.get_memory_usage()
            
            duration = end_time - start_time
            mem_delta = mem_after - mem_before
            posts_per_sec = len(posts) / duration if duration > 0 else 0
            
            result = {
                "platform": "Reddit",
                "posts_scraped": len(posts),
                "duration_seconds": round(duration, 2),
                "posts_per_second": round(posts_per_sec, 2),
                "memory_delta_mb": round(mem_delta, 2),
                "status": "success"
            }
            
            print(f"✅ Scraped {len(posts)} posts in {duration:.2f}s")
            print(f"   Speed: {posts_per_sec:.2f} posts/sec")
            print(f"   Memory: +{mem_delta:.2f} MB")
            
            self.results['reddit'] = result
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['reddit'] = {"status": "error", "error": str(e)}
            return None
    
    def benchmark_linkedin_scraping(self, query="artificial intelligence", limit=10):
        """Benchmark LinkedIn scraping performance"""
        print(f"\n🔍 Benchmarking LinkedIn scraping ({limit} posts)...")
        print("=" * 60)
        
        mem_before = self.get_memory_usage()
        start_time = time.time()
        
        try:
            scraper = LinkedInScraper()
            posts = scraper.search_content(
                keywords=query,
                search_type="keywords",
                max_posts=limit
            )
            
            end_time = time.time()
            mem_after = self.get_memory_usage()
            
            duration = end_time - start_time
            mem_delta = mem_after - mem_before
            posts_per_sec = len(posts) / duration if duration > 0 else 0
            
            result = {
                "platform": "LinkedIn",
                "posts_scraped": len(posts),
                "duration_seconds": round(duration, 2),
                "posts_per_second": round(posts_per_sec, 2),
                "memory_delta_mb": round(mem_delta, 2),
                "status": "success"
            }
            
            print(f"✅ Scraped {len(posts)} posts in {duration:.2f}s")
            print(f"   Speed: {posts_per_sec:.2f} posts/sec")
            print(f"   Memory: +{mem_delta:.2f} MB")
            
            self.results['linkedin'] = result
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['linkedin'] = {"status": "error", "error": str(e)}
            return None
    
    def benchmark_db_insertion(self, num_posts=100):
        """Benchmark database insertion speed"""
        print(f"\n💾 Benchmarking DB insertion ({num_posts} posts)...")
        print("=" * 60)
        
        store = DataStore()
        
        # Generate test data
        test_posts = []
        for i in range(num_posts):
            test_posts.append({
                "id": f"test_post_{i}_{int(time.time())}",
                "platform": "test",
                "title": f"Test Post {i}",
                "content": f"This is test content for post {i}",
                "author": f"test_user_{i}",
                "url": f"https://example.com/post/{i}",
                "metrics": {"score": i * 10},
                "created_at": datetime.now(),
                "is_test_data": True
            })
        
        mem_before = self.get_memory_usage()
        start_time = time.time()
        
        inserted = 0
        for post in test_posts:
            if store.insert_post(post):
                inserted += 1
        
        end_time = time.time()
        mem_after = self.get_memory_usage()
        
        duration = end_time - start_time
        mem_delta = mem_after - mem_before
        inserts_per_sec = inserted / duration if duration > 0 else 0
        
        result = {
            "operation": "DB Insertion",
            "posts_inserted": inserted,
            "duration_seconds": round(duration, 2),
            "inserts_per_second": round(inserts_per_sec, 2),
            "memory_delta_mb": round(mem_delta, 2),
            "status": "success"
        }
        
        print(f"✅ Inserted {inserted} posts in {duration:.2f}s")
        print(f"   Speed: {inserts_per_sec:.2f} inserts/sec")
        print(f"   Memory: +{mem_delta:.2f} MB")
        
        # Cleanup test data
        store.db.posts.delete_many({"is_test_data": True})
        
        self.results['db_insertion'] = result
        return result
    
    def print_summary(self):
        """Print comprehensive benchmark summary"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)
        
        if 'reddit' in self.results and self.results['reddit'].get('status') == 'success':
            r = self.results['reddit']
            print(f"\n🔴 Reddit:")
            print(f"  Posts: {r['posts_scraped']}")
            print(f"  Time: {r['duration_seconds']}s")
            print(f"  Speed: {r['posts_per_second']} posts/sec")
            print(f"  Memory: +{r['memory_delta_mb']} MB")
        
        if 'linkedin' in self.results and self.results['linkedin'].get('status') == 'success':
            l = self.results['linkedin']
            print(f"\n💼 LinkedIn:")
            print(f"  Posts: {l['posts_scraped']}")
            print(f"  Time: {l['duration_seconds']}s")
            print(f"  Speed: {l['posts_per_second']} posts/sec")
            print(f"  Memory: +{l['memory_delta_mb']} MB")
        
        if 'db_insertion' in self.results and self.results['db_insertion'].get('status') == 'success':
            d = self.results['db_insertion']
            print(f"\n💾 Database:")
            print(f"  Inserts: {d['posts_inserted']}")
            print(f"  Time: {d['duration_seconds']}s")
            print(f"  Speed: {d['inserts_per_second']} inserts/sec")
            print(f"  Memory: +{d['memory_delta_mb']} MB")
        
        print("\n" + "=" * 60)

def main():
    print("🚀 Performance Benchmarking Tool")
    print("Testing scraping and database performance...\n")
    
    benchmark = PerformanceBenchmark()
    
    # Run benchmarks
    print(f"💻 System Info:")
    print(f"  CPU Count: {psutil.cpu_count()}")
    print(f"  Memory Total: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")
    print(f"  Memory Available: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.2f} GB")
    
    # Reddit benchmark
    benchmark.benchmark_reddit_scraping(limit=10)
    
    # LinkedIn benchmark (skip if credentials not available)
    benchmark.benchmark_linkedin_scraping(limit=5)
    
    # Database benchmark
    benchmark.benchmark_db_insertion(num_posts=50)
    
    # Summary
    benchmark.print_summary()
    
    print("\n✨ Benchmarking complete!")

if __name__ == "__main__":
    main()

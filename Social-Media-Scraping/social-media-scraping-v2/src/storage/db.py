# src/storage/db.py
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv

class DataStore:
    def __init__(self, mongo_uri: str = None):
        load_dotenv()  # Load environment variables
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client["social_media_db"]
        self.init_db()
    
    def init_db(self):
        """Create collections and indexes"""
        # Posts collection
        if "posts" not in self.db.list_collection_names():
            self.db.create_collection("posts")
        
        # Create unique index on (id, platform) to prevent duplicates
        self.db.posts.create_index([("id", 1), ("platform", 1)], unique=True)
        self.db.posts.create_index("created_at")
        self.db.posts.create_index("platform")
        
        # Keywords collection
        if "scraped_keywords" not in self.db.list_collection_names():
            self.db.create_collection("scraped_keywords")
        
        self.db.scraped_keywords.create_index("keyword")
    
    def insert_post(self, post_data: dict) -> bool:
        """Insert a post, skip if duplicate"""
        try:
            # Use the post_data structure as-is (enhanced format from frontend)
            # or fall back to old format for backward compatibility
            if "metrics" in post_data:
                # New enhanced format - store as-is
                self.db.posts.insert_one(post_data)
            else:
                # Old format - convert to legacy structure for compatibility
                self.db.posts.insert_one({
                    "id": post_data.get("id"),
                    "platform": post_data.get("platform"),
                    "title": post_data.get("title"),
                    "content": post_data.get("content", post_data.get("text")),
                    "author": post_data.get("author"),
                    "source_url": post_data.get("url"),
                    "engagement_metrics": post_data.get("metrics", {}),
                    "created_at": post_data.get("created_at"),
                    "scraped_at": datetime.now()
                })
            return True
        except DuplicateKeyError:
            return False  # Duplicate
    
    def search_posts(self, keyword: str, limit: int = 100) -> List[Dict]:
        """Search stored posts"""
        results = list(self.db.posts.find(
            {"$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"content": {"$regex": keyword, "$options": "i"}}
            ]},
            sort=[("created_at", -1)],
            limit=limit
        ))
        return results
    
    def filter_by_platform(self, platform: str, limit: int = 100) -> List[Dict]:
        """Get posts from specific platform"""
        results = list(self.db.posts.find(
            {"platform": platform},
            sort=[("created_at", -1)],
            limit=limit
        ))
        return results
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        return {
            "total_posts": self.db.posts.count_documents({}),
            "platforms": list(self.db.posts.distinct("platform")),
            "by_platform": [
                {"platform": p, "count": self.db.posts.count_documents({"platform": p})}
                for p in self.db.posts.distinct("platform")
            ]
        }

# Usage
if __name__ == "__main__":
    store = DataStore()
    post = {
        "id": "tweet_123",
        "platform": "twitter",
        "title": "Apple News",
        "content": "New M4 chip announced",
        "author": "@user",
        "url": "https://twitter.com/...",
        "metrics": {"likes": 150, "retweets": 45},
        "created_at": datetime.now()
    }
    store.insert_post(post)
    print(store.get_stats())
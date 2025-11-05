#!/usr/bin/env python3
"""
Quick test script to verify API credentials and connections
"""
import os
from dotenv import load_dotenv
import requests
import praw

# Load environment variables
load_dotenv()

def test_twitter_api():
    """Test Twitter API connection"""
    print("🐦 Testing Twitter API...")
    
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        print("❌ No Twitter bearer token found")
        return False
    
    headers = {"Authorization": f"Bearer {bearer_token}"}
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": "hello",
        "max_results": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            tweets_count = len(data.get("data", []))
            print(f"✅ Twitter API working! Found {tweets_count} tweets")
            return True
        else:
            print(f"❌ Twitter API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Twitter API exception: {e}")
        return False

def test_reddit_api():
    print("\n🔴 Testing Reddit API...")
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    
    if not all([client_id, client_secret, user_agent]):
        print("❌ Missing Reddit credentials")
        return False
    
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Test by getting a few posts from r/test
        subreddit = reddit.subreddit("test")
        posts = list(subreddit.new(limit=2))
        
        print(f"✅ Reddit API working! Found {len(posts)} posts in r/test")
        return True
        
    except Exception as e:
        print(f"❌ Reddit API exception: {e}")
        return False

def test_mongodb():
    """Test MongoDB connection"""
    print("\n🍃 Testing MongoDB connection...")
    
    try:
        from pymongo import MongoClient
        
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            print("❌ No MongoDB URI found")
            return False
        
        client = MongoClient(mongo_uri)
        # Test connection
        client.admin.command('ping')
        
        print("✅ MongoDB connection working!")
        return True
        
    except Exception as e:
        print(f"❌ MongoDB exception: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing API Connections...\n")
    
    twitter_ok = test_twitter_api()
    reddit_ok = test_reddit_api() 
    mongo_ok = test_mongodb()
    
    print(f"\n📊 Results:")
    print(f"Twitter: {'✅' if twitter_ok else '❌'}")
    print(f"Reddit: {'✅' if reddit_ok else '❌'}")
    print(f"MongoDB: {'✅' if mongo_ok else '❌'}")
    
    if all([twitter_ok, reddit_ok, mongo_ok]):
        print("\n🎉 All APIs working! Ready to scrape!")
    else:
        print("\n⚠️  Some APIs need fixing before scraping")
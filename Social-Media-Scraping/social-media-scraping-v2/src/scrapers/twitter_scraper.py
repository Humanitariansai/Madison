import requests
import os
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from utils.rate_limiter import rate_limiter

class TwitterScraper:
    def __init__(self):
        load_dotenv()  # Load environment variables
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.base_url = "https://api.twitter.com/2"
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"}
    
    def search_tweets(self, query: str, max_results: int = 100) -> List[Dict]:
        """Search recent tweets by keyword"""
        rate_limiter.wait_if_needed('twitter')  # Rate limiting
        
        url = f"{self.base_url}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,author_id"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            print(f"Twitter API error: {e}")
            return []
    
    def get_trending_topics(self) -> List[Dict]:
        """Get trending topics (requires elevated access)"""
        # Note: This requires Academic Research access
        # For now, we'll use search as a workaround
        pass

# Usage
if __name__ == "__main__":
    scraper = TwitterScraper()
    tweets = scraper.search_tweets("Apple", max_results=50)
    for tweet in tweets:
        print(f"{tweet['created_at']}: {tweet['text']}")
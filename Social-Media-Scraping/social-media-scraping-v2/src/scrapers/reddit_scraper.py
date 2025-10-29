# src/scrapers/reddit_scraper.py
import praw
import os
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
from utils.rate_limiter import rate_limiter

class RedditScraper:
    def __init__(self):
        load_dotenv()  # Load environment variables
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "SocialMediaScraper/1.0")
        )
    
    def search_subreddits(self, query: str, limit: int = 100) -> List[Dict]:
        """Search across subreddits"""
        rate_limiter.wait_if_needed('reddit')  # Rate limiting
        
        posts = []
        try:
            for submission in self.reddit.subreddit("all").search(query, time_filter="week", limit=limit):
                posts.append({
                    # Basic info
                    "id": submission.id,
                    "title": submission.title,
                    "text": submission.selftext,
                    "subreddit": submission.subreddit.display_name,
                    "author": str(submission.author),
                    "url": submission.url,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "domain": submission.domain,
                    
                    # Engagement metrics
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "comments": submission.num_comments,
                    "gilded": submission.gilded,
                    "total_awards": submission.total_awards_received,
                    
                    # Content classification
                    "nsfw": submission.over_18,
                    "spoiler": submission.spoiler,
                    "stickied": submission.stickied,
                    "locked": submission.locked,
                    "archived": submission.archived,
                    "distinguished": submission.distinguished,
                    
                    # Media info
                    "is_video": submission.is_video,
                    "is_original_content": submission.is_original_content,
                    "is_self": submission.is_self,
                    
                    # Flair and categorization
                    "link_flair_text": submission.link_flair_text,
                    "link_flair_css_class": submission.link_flair_css_class,
                    "author_flair_text": submission.author_flair_text,
                    
                    # Timestamps
                    "created_at": datetime.fromtimestamp(submission.created_utc),
                    "edited": datetime.fromtimestamp(submission.edited) if submission.edited else None,
                })
        except Exception as e:
            print(f"Reddit scraping error: {e}")
        
        return posts
    
    def get_subreddit_posts(self, subreddit: str, limit: int = 50) -> List[Dict]:
        """Get recent posts from a specific subreddit"""
        rate_limiter.wait_if_needed('reddit')  # Rate limiting
        
        posts = []
        try:
            sub = self.reddit.subreddit(subreddit)
            for submission in sub.new(limit=limit):
                posts.append({
                    # Basic info
                    "id": submission.id,
                    "title": submission.title,
                    "text": submission.selftext,
                    "subreddit": submission.subreddit.display_name,
                    "author": str(submission.author),
                    "url": submission.url,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "domain": submission.domain,
                    
                    # Engagement metrics
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "comments": submission.num_comments,
                    "gilded": submission.gilded,
                    "total_awards": submission.total_awards_received,
                    
                    # Content classification
                    "nsfw": submission.over_18,
                    "spoiler": submission.spoiler,
                    "stickied": submission.stickied,
                    "locked": submission.locked,
                    "archived": submission.archived,
                    "distinguished": submission.distinguished,
                    
                    # Media info
                    "is_video": submission.is_video,
                    "is_original_content": submission.is_original_content,
                    "is_self": submission.is_self,
                    
                    # Flair and categorization
                    "link_flair_text": submission.link_flair_text,
                    "link_flair_css_class": submission.link_flair_css_class,
                    "author_flair_text": submission.author_flair_text,
                    
                    # Timestamps
                    "created_at": datetime.fromtimestamp(submission.created_utc),
                    "edited": datetime.fromtimestamp(submission.edited) if submission.edited else None,
                })
        except Exception as e:
            print(f"Subreddit error: {e}")
        
        return posts

# Usage
if __name__ == "__main__":
    scraper = RedditScraper()
    results = scraper.search_subreddits("Apple", limit=50)
    for post in results:
        print(f"r/{post['subreddit']}: {post['title']} ({post['score']} upvotes)")
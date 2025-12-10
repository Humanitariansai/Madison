import praw
import os
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
from src.utils.rate_limiter import rate_limiter

class RedditScraper:
    def __init__(self):
        load_dotenv()
        
        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        
        # Region-specific subreddits mapping
        self.region_subreddits = {
            "North America": ["usa", "canada", "mexico", "northamerica"],
            "Europe": ["europe", "europeans", "eu", "ukpolitics", "germany", "france", "italy"],
            "Asia": ["asia", "china", "india", "japan", "korea", "singapore"],
            "Oceania": ["australia", "newzealand", "oceania"],
            "South America": ["brazil", "argentina", "chile", "southamerica"],
            "Africa": ["africa", "southafrica", "nigeria", "kenya"],
            "Global": ["all", "popular", "worldnews", "news"]
        }
    
    def _get_region_subreddits(self, regions: List[str]) -> str:
        """Get subreddit string for specified regions"""
        if not regions or "All" in regions or "Global" in regions:
            return "all"
        
        selected_subs = []
        for region in regions:
            if region in self.region_subreddits:
                selected_subs.extend(self.region_subreddits[region])
        
        return "+".join(selected_subs) if selected_subs else "all"
    
    def search_subreddits(
        self, 
        query: str, 
        limit: int = 100, 
        time_filter: str = "week",
        start_date: datetime = None,
        end_date: datetime = None,
        min_upvotes: int = 0,
        regions: List[str] = None,
        include_subreddits: List[str] = None,
        exclude_subreddits: List[str] = None,
        sort: str = "relevance",
        search_scope: str = "title_body",
    ) -> List[Dict]:
        rate_limiter.wait_if_needed('reddit')  # Rate limiting
        
        posts = []
        try:
            # Handle custom date range
            if time_filter == "custom" and start_date and end_date:
                search_time_filter = "all"
            else:
                search_time_filter = time_filter

            # Get region-specific subreddits
            region_subreddits = self._get_region_subreddits(regions) if regions else "all"
            
            filtered_posts = []
            for submission in self.reddit.subreddit(region_subreddits).search(
                query,
                time_filter=search_time_filter,
                limit=limit*2,
                sort=sort if sort in ["relevance", "new", "top", "comments"] else None,
            ):
                # Apply minimum upvotes filter
                if submission.score < min_upvotes:
                    continue

                # Subreddit include/exclude filters
                sub_name = submission.subreddit.display_name.lower()
                if include_subreddits:
                    if sub_name not in {s.lower() for s in include_subreddits}:
                        continue
                if exclude_subreddits:
                    if sub_name in {s.lower() for s in exclude_subreddits}:
                        continue

                # Optional title-only scope
                if search_scope == "title":
                    if query.lower() not in (submission.title or "").lower():
                        continue
                
                # Apply custom date range filter if specified
                if time_filter == "custom" and start_date and end_date:
                    submission_date = datetime.fromtimestamp(submission.created_utc).date()
                    if not (start_date <= submission_date <= end_date):
                        continue
                
                # If post passes all filters, add it to filtered posts
                filtered_posts.append(submission)
                if len(filtered_posts) >= limit:
                    break
            
            # Apply local sorting if requested (score/comments/new) to stabilize ordering
            if sort in ["score", "comments", "new"]:
                if sort == "score":
                    filtered_posts.sort(key=lambda s: s.score, reverse=True)
                elif sort == "comments":
                    filtered_posts.sort(key=lambda s: s.num_comments, reverse=True)
                elif sort == "new":
                    filtered_posts.sort(key=lambda s: s.created_utc, reverse=True)

            # Process filtered posts
            for submission in filtered_posts[:limit]:
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
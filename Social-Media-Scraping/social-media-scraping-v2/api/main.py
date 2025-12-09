from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
from datetime import date

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.storage.db import DataStore
from src.scrapers.reddit_scraper import RedditScraper

app = FastAPI(
    title="Social Media Scraper API",
    version="1.0",
    description="API for Reddit and LinkedIn social media scraping"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database connection
store = DataStore()
reddit_scraper = RedditScraper()

@app.get("/")
def root():
    """Root endpoint - health check"""
    return {
        "status": "online",
        "message": "Social Media Scraper API",
        "version": "1.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    try:
        store.get_stats()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

class Post(BaseModel):
    id: str
    platform: str
    content: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None


@app.get("/reddit/search")
def search_reddit(
    query: str = Query(..., min_length=1, description="Keyword or brand to search for"),
    limit: int = Query(30, ge=1, le=100, description="Maximum number of posts to return"),
    time_filter: str = Query(
        "week",
        regex="^(hour|day|week|month|year|all|custom)$",
        description="Reddit time filter; use 'custom' with start_date and end_date",
    ),
    start_date: Optional[date] = Query(None, description="Start date for custom range (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for custom range (YYYY-MM-DD)"),
    min_upvotes: int = Query(0, ge=0, description="Minimum score threshold"),
    regions: Optional[str] = Query(
        None,
        description="Comma-separated regions (Global, North America, Europe, Asia, Oceania, South America, Africa)",
    ),
):
    """Search Reddit posts via RedditScraper with optional filters."""
    if time_filter == "custom" and (not start_date or not end_date):
        raise HTTPException(status_code=400, detail="Provide start_date and end_date for custom time_filter")

    region_list = None
    if regions:
        region_list = [region.strip() for region in regions.split(",") if region.strip()]

    try:
        posts = reddit_scraper.search_subreddits(
            query=query,
            limit=limit,
            time_filter=time_filter,
            start_date=start_date,
            end_date=end_date,
            min_upvotes=min_upvotes,
            regions=region_list,
        )
        return {"total": len(posts), "posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reddit search failed: {str(e)}")

@app.get("/posts")
def get_posts(platform: Optional[str] = None, limit: int = 100):
    """Retrieve posts, optionally filtered by platform."""
    try:
        if platform:
            posts = store.filter_by_platform(platform, limit=limit)
        else:
            posts = list(store.db.posts.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))
        return {"total": len(posts), "posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching posts: {str(e)}")

@app.get("/stats")
def get_stats():
    """Retrieve basic statistics about the posts."""
    try:
        stats = store.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.post("/posts")
def create_post(post: Dict[Any, Any]):
    """Add a new post to the database."""
    try:
        success = store.insert_post(post)
        if not success:
            raise HTTPException(status_code=400, detail="Post with this ID already exists.")
        return {"status": "success", "post": post}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting post: {str(e)}")

@app.get("/linkedin/posts")
def get_linkedin_posts(limit: int = 100, author: Optional[str] = None):
    """Retrieve LinkedIn posts, optionally filtered by author."""
    try:
        query = {}
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
        
        posts = list(store.db.linkedin_posts.find(query, {"_id": 0}).sort("scraped_at", -1).limit(limit))
        return {"total": len(posts), "posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching LinkedIn posts: {str(e)}")

@app.get("/linkedin/stats")
def get_linkedin_stats():
    """Retrieve LinkedIn posts statistics."""
    try:
        stats = store.get_linkedin_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching LinkedIn stats: {str(e)}")

@app.get("/export")
def export_posts(platform: Optional[str] = None):
    """Export posts as a CSV file."""
    import csv
    from fastapi.responses import StreamingResponse
    from io import StringIO

    try:
        if platform:
            posts = store.filter_by_platform(platform, limit=10000)
        else:
            posts = list(store.db.posts.find({}, {"_id": 0}).limit(10000))
        
        if not posts:
            raise HTTPException(status_code=404, detail="No posts found")
        
        output = StringIO()
        fieldnames = ["id", "platform", "title", "content", "author", "created_at"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for post in posts:
            # Convert datetime to string if present
            if "created_at" in post and post["created_at"]:
                post["created_at"] = str(post["created_at"])
            writer.writerow(post)
        
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=posts.csv"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting posts: {str(e)}")

@app.get("/linkedin/export")
def export_linkedin_posts(author: Optional[str] = None):
    """Export LinkedIn posts as a CSV file."""
    import csv
    from fastapi.responses import StreamingResponse
    from io import StringIO

    try:
        query = {}
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
        
        posts = list(store.db.linkedin_posts.find(query, {"_id": 0}).limit(10000))
        
        if not posts:
            raise HTTPException(status_code=404, detail="No LinkedIn posts found")
        
        output = StringIO()
        fieldnames = ["author", "author_headline", "content", "posted_time", "link", "likes", "comments", "reposts", "scraped_at"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for post in posts:
            # Flatten metrics
            if "metrics" in post:
                post.update({
                    "likes": post["metrics"].get("likes", 0),
                    "comments": post["metrics"].get("comments", 0),
                    "reposts": post["metrics"].get("reposts", 0)
                })
            # Convert datetime to string
            if "scraped_at" in post and post["scraped_at"]:
                post["scraped_at"] = str(post["scraped_at"])
            writer.writerow(post)
        
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=linkedin_posts.csv"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting LinkedIn posts: {str(e)}")
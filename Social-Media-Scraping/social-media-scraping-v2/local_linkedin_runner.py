#!/usr/bin/env python3
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv

# Robust import path for src
try:
    from src.scrapers.linkedin_scraper import LinkedInScraper
except Exception:
    import sys
    from pathlib import Path
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from scrapers.linkedin_scraper import LinkedInScraper

load_dotenv()

app = FastAPI(title="Local LinkedIn Runner", version="1.0")

class ScrapeRequest(BaseModel):
    keywords: List[str]
    search_type: str = "keywords"  # or "hashtag"
    max_posts: int = 10
    verification_code: Optional[str] = None
    debug: bool = False

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/scrape")
def scrape(req: ScrapeRequest, x_auth_token: Optional[str] = Header(None)):
    # Simple shared-secret auth
    expected = os.getenv("LINKEDIN_RUNNER_TOKEN")
    if expected:
        if not x_auth_token or x_auth_token != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        scraper = LinkedInScraper()
        results = scraper.search_content(
            keywords=req.keywords if req.search_type != "hashtag" else req.keywords[0],
            search_type=req.search_type,
            max_posts=req.max_posts,
            debug=req.debug,
            verification_code=req.verification_code,
        )
        # Close browser promptly
        try:
            scraper.close()
        except Exception:
            pass
        return {"count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("local_linkedin_runner:app", host="127.0.0.1", port=9000, reload=False)

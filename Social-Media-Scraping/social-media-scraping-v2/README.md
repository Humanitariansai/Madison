# Social Media Scraping v2

A robust, ethical social media data collection tool that scrapes public data from multiple platforms for sentiment analysis, trend tracking, and market research.

## 🚀 Features

- **Multi-Platform Support**: Reddit and LinkedIn
- **Production-Ready UI**: Streamlit-based, dark theme, accessible nav (radio with hidden label)
- **Results View**: Browse saved Reddit/LinkedIn posts with keyword filter and row limit
- **Session Stability**: LinkedIn table view persists across reruns; sidebar only on Search
- **Ethical Scraping**: Rate limiting, public data only
- **Robust Storage**: MongoDB with duplicate detection (content-hash for LinkedIn, ID for Reddit)
- **LinkedIn Runner**: Local FastAPI runner on `:9000`, works with Cloudflared Quick Tunnel
- **Analytics**: Engagement metrics available in UI and via API

Notes
- UI export buttons were removed per UX feedback; CSV export is available via API endpoints.

## 🛠 Tech Stack

- **Language**: Python 3.11
- **UI**: Streamlit 1.28.x (custom dark theme via `.streamlit/config.toml`)
- **API**: FastAPI + Uvicorn (local LinkedIn runner and REST API)
- **Scraping**: Selenium 4 + webdriver-manager, PRAW for Reddit
- **Parsing**: BeautifulSoup4, lxml
- **Data**: MongoDB (Atlas or local) via PyMongo
- **Utilities**: pandas, python-dotenv, psutil
- **Tunneling**: Cloudflared (Quick Tunnel) for sharing local runner
- **Container**: Dockerfile + Render deployment (free plan supported)

## 📁 Project Structure

```
social-media-scraping-v2/
├── src/
│   ├── scrapers/
│   │   ├── linkedin_scraper.py   # LinkedIn Selenium-based scraper
│   │   └── reddit_scraper.py     # Reddit PRAW integration
│   ├── storage/
│   │   └── db.py                 # MongoDB data storage (posts + linkedin_posts)
│   └── utils/
│       ├── rate_limiter.py       # API rate limiting
│       └── config.py             # Utility config helpers
├── api/
│   ├── main.py                   # REST API (stats, posts, exports)
│   └── webhooks.py               # Webhook endpoints
├── app_combined.py               # Combined Reddit + LinkedIn app (recommended)
├── app.py                        # Legacy Reddit-focused Streamlit app (optional)
├── app_v2.py                     # Legacy LinkedIn-only Streamlit app (optional)
├── local_linkedin_runner.py      # Local FastAPI runner for LinkedIn scraping (:9000)
├── .streamlit/config.toml        # Dark theme and Streamlit settings
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Containerized Streamlit app
├── render.yaml                   # Render deployment configuration
└── README.md                     # This file
```

## ⚡ Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd social-media-scraping-v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root with your credentials:

```env
# Reddit API (get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID="your_reddit_client_id"
REDDIT_CLIENT_SECRET="your_reddit_client_secret"
REDDIT_USER_AGENT="SocialMediaScraper/1.0"

# LinkedIn Credentials (your personal LinkedIn account)
LINKEDIN_USERNAME="your_email@example.com"
LINKEDIN_PASSWORD="your_linkedin_password"

# Optional: shared secret for local runner
LINKEDIN_RUNNER_TOKEN="some-secret"

# MongoDB (Atlas or local)
MONGODB_URI="mongodb://localhost:27017"
# OR for MongoDB Atlas:
# MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
```

**Security Note**: Never commit your `.env` file. It's already in `.gitignore`.

### 3. Usage

#### Option A: Streamlit UI (Recommended)

Run the combined app supporting both Reddit and LinkedIn:

```bash
streamlit run app_combined.py
```

Or run platform-specific apps:

```bash
# LinkedIn-only scraper
streamlit run app_v2.py

# Reddit-focused scraper with DB integration
streamlit run app.py
```

**Features in Streamlit UI:**
- Pill-style Search/Results navigation (accessible radio; label hidden)
- Sidebar visible only on Search; Results shows saved posts
- Keyword filter and row limit for Results
- Real-time progress and engagement metrics
- Save to MongoDB with duplicate detection
- No UI export buttons; use API export endpoints if needed

#### Option B: Programmatic Usage

**Reddit Scraping:**

```python
from src.scrapers.reddit_scraper import RedditScraper
from src.storage.db import DataStore

# Initialize
reddit = RedditScraper()
store = DataStore()

# Scrape Reddit posts
posts = reddit.search_subreddits(
    query="Python programming",
    limit=20,
    time_filter="week",
    min_upvotes=10
)

# Save to MongoDB (posts collection)
for post in posts:
    store.insert_post({
        "id": post["id"],
        "platform": "reddit",
        "title": post["title"],
        "content": post["text"],
        "author": post["author"],
        "url": post["url"],
        "subreddit": post["subreddit"],
        "metrics": {
            "score": post["score"],
            "comments": post["comments"],
            "upvote_ratio": post.get("upvote_ratio")
        },
        "created_at": post["created_at"],
        "scraped_at": datetime.now()
    })
```

**LinkedIn Scraping (Programmatic):**

```python
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.storage.db import DataStore
import hashlib
from datetime import datetime

# Initialize
linkedin = LinkedInScraper()
store = DataStore()

# Search LinkedIn posts
posts = linkedin.search_content(
    keywords="artificial intelligence",
    search_type="keywords",
    max_posts=10
)

# Save to MongoDB (linkedin_posts collection)
for post in posts:
    content_hash = hashlib.md5(
        f"{post.get('author', '')}_{post.get('content', '')}_{post.get('posted_time', '')}".encode()
    ).hexdigest()
    
    store.insert_linkedin_post({
        "content_hash": content_hash,
        "author": post.get("author"),
        "content": post.get("content"),
        "link": post.get("link"),
        "metrics": {
            "likes": post.get("likes", 0),
            "comments": post.get("comments", 0),
            "reposts": post.get("reposts", 0)
        },
        "scraped_at": datetime.now()
    })
```

### 4. LinkedIn Local Runner + Cloudflared

Run the LinkedIn runner locally (port 9000):

```bash
python local_linkedin_runner.py
```

Share it with a temporary public URL using Cloudflared Quick Tunnel:

```bash
cloudflared tunnel --url http://localhost:9000
```

The tunnel output prints a `https://<random>.trycloudflare.com` URL you can call from the UI or external tools. For a permanent hostname, you need a domain on Cloudflare and a Named Tunnel.

### 5. Testing

```bash
# Run integration tests (covers Reddit + LinkedIn)
pytest tests/test_integration.py -v

# Run all tests
pytest tests/ -v

# Test API connections
python test_apis.py
```

## 📊 Data Schema

### MongoDB Collections

The system uses two separate collections:

1. **`posts`** - Reddit posts
2. **`linkedin_posts`** - LinkedIn posts

### Reddit Post Document (posts collection)

```json
{
  "id": "reddit_post_id",
  "platform": "reddit",
  "title": "Post title",
  "content": "Full post text",
  "author": "reddit_username",
  "url": "https://reddit.com/...",
  "permalink": "/r/subreddit/comments/...",
  "subreddit": "Python",
  "metrics": {
    "score": 250,
    "comments": 42,
    "upvote_ratio": 0.95,
    "gilded": 1,
    "total_awards": 3
  },
  "content_flags": {
    "nsfw": false,
    "spoiler": false,
    "is_video": false,
    "is_self": true
  },
  "flair": {
    "link_flair_text": "Discussion",
    "author_flair_text": "Contributor"
  },
  "created_at": "2025-11-10T12:00:00Z",
  "scraped_at": "2025-11-10T12:05:00Z",
  "search_brand": "Python",
  "scraped_via": "streamlit_combined"
}
```

### LinkedIn Post Document (linkedin_posts collection)

```json
{
  "content_hash": "abc123def456...",
  "author": "John Doe",
  "author_headline": "AI Engineer at TechCorp",
  "content": "Excited to share our latest project on...",
  "posted_time": "1w",
  "link": "https://www.linkedin.com/feed/update/...",
  "metrics": {
    "likes": 150,
    "comments": 23,
    "reposts": 12,
    "total_engagement": 185
  },
  "search_query": "artificial intelligence",
  "scraped_via": "streamlit_app_v2",
  "scraped_at": "2025-11-10T12:05:00Z"
}
```

## 🔧 API Reference

### RedditScraper

```python
from src.scrapers.reddit_scraper import RedditScraper

scraper = RedditScraper()

# Search across all subreddits with filters
posts = scraper.search_subreddits(
    query="keyword",
    limit=100,
    time_filter="week",  # "hour", "day", "week", "month", "year", "all"
    min_upvotes=10,
    regions=["North America", "Europe"]  # Optional region filtering
)

# Get posts from specific subreddit
posts = scraper.get_subreddit_posts("python", limit=50)
```

### LinkedInScraper

```python
from src.scrapers.linkedin_scraper import LinkedInScraper

scraper = LinkedInScraper()

# Search by keywords
posts = scraper.search_content(
    keywords="machine learning",
    search_type="keywords",  # or "hashtag"
    max_posts=20,
    debug=False
)

# Search by hashtag
posts = scraper.search_content(
    keywords="AI",
    search_type="hashtag",
    max_posts=15
)
```

### DataStore

```python
from src.storage.db import DataStore

store = DataStore()

# Insert Reddit post (with duplicate detection via id+platform)
success = store.insert_post(reddit_post_data)

# Insert LinkedIn post (with duplicate detection via content_hash)
success = store.insert_linkedin_post(linkedin_post_data)

# Search stored Reddit posts
results = store.search_posts("keyword", limit=100)

# Filter by platform
results = store.filter_by_platform("reddit", limit=100)

# Get general statistics
stats = store.get_stats()
# Returns: {
#   "total_posts": 1250,          # Reddit posts count
#   "linkedin_posts": 340,         # LinkedIn posts count
#   "platforms": ["reddit"],
#   "by_platform": [{"platform": "reddit", "count": 1250}]
# }

# Get LinkedIn-specific statistics
linkedin_stats = store.get_linkedin_stats()
# Returns: {
#   "total_posts": 340,
#   "unique_authors": 187
# }
```

## 🚀 New Features

### RESTful API
- **Endpoints**:
  - `/posts`: Retrieve posts (filter by platform optional).
  - `/stats`: View post statistics.
  - `/export`: Download posts as CSV.

### Webhook System
- **Endpoints**:
  - `/webhook`: Receive webhook events.
  - `/webhook/events`: List received events.
  - `/webhook/notify`: Send webhook notifications.

### Performance Optimization
- Added async scraping for Reddit.
- Benchmarks now include async performance metrics.

### How to Run
1. **Start API**:
   ```bash
   uvicorn api.main:app --reload
   ```
2. **Start Webhook System**:
   ```bash
   uvicorn api.webhooks:app --reload
   ```
3. **Run Benchmarks**:
   ```bash
   python src/tools/benchmark.py
   ```

### Next Steps
- Add security headers and rate limiting.
- Finalize soft launch with sample datasets.

## 🛡️ Ethical Guidelines

This tool follows strict ethical guidelines:

- **Public Data Only**: Only scrapes publicly available content
- **Rate Limiting**: Respects platform API limits and terms of service
- **No Personal Data**: Avoids collecting sensitive personal information
- **Robots.txt Compliance**: Respects website scraping preferences
- **Data Anonymization**: Options to anonymize user data

See [ETHICAL_GUIDELINES.md](ethics/ETHICAL_GUIDELINES.md) for full details.

## 🔍 Troubleshooting

### Reddit API Issues

- **Missing Credentials**: Ensure all Reddit environment variables are set in `.env`
- **Rate Limiting**: Reddit allows ~100 requests per minute
- **401 Unauthorized**: Check `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
- **No Results**: Try broader keywords or different time filters

### LinkedIn Scraper Issues

- **Login Failed**: Verify `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD` in `.env`
- **Selenium WebDriver Error**: 
  ```bash
  # Install/update ChromeDriver
  pip install --upgrade webdriver-manager
  ```
- **Empty Results**: LinkedIn may require manual CAPTCHA solving; run in non-headless mode for debugging
- **Timeout Errors**: Increase wait times in `linkedin_scraper.py` or check your internet connection
- **Rate Limiting**: LinkedIn may temporarily block automated access; wait 15-30 minutes and reduce scraping frequency

### MongoDB Issues

- **Connection Failed**: 
  - Check your MongoDB URI and network access
  - For local MongoDB: ensure `mongod` is running
  - For Atlas: verify IP whitelist and network connectivity
- **Authentication Failed**: Verify username/password in connection string
- **Duplicate Key Error**: Normal behavior - indicates the post already exists in the database

### Streamlit App Issues

- Clear cache quickly from code:
  ```python
  import streamlit as st
  st.cache_data.clear(); st.cache_resource.clear(); st.session_state.clear(); st.rerun()
  ```

- **`DuplicateWidgetID` Error**: Fixed in latest version; ensure you're running updated `app_combined.py` or `app_v2.py`
- **Import Errors**: 
  ```bash
  # Reinstall dependencies
  pip install -r requirements.txt
  ```
- **Port Already in Use**: Change port with `streamlit run app_combined.py --server.port 8502`

## 📈 Development Roadmap

### Week 1-2 ✅ (Completed)
- [x] Repository setup
- [x] Reddit scraper (PRAW)
- [x] LinkedIn scraper (Selenium-based)
- [x] Data storage system (MongoDB with separate collections)
- [x] Duplicate detection (ID-based for Reddit, content-hash for LinkedIn)
- [x] Integration tests
- [x] Rate limiting

### Week 3 ✅ (Completed)
- [x] Streamlit UI (3 versions: Reddit, LinkedIn, Combined)
- [x] CSV export functionality
- [x] Real-time analytics dashboard
- [x] Save-to-database functionality
- [x] Search history tracking
- [x] Card-based and table view results

### Current Sprint (In Progress)
- [x] Usage examples and documentation
- [ ] Performance testing and optimization
- [ ] Webhook system (planned)
- [ ] RESTful API (planned)

### Future Enhancements
- [ ] Instagram scraper (public profiles)
- [ ] Advanced rate limiting with backoff strategies
- [ ] Data processing pipeline (sentiment analysis, NLP)
- [ ] Scheduled scraping with cron jobs
- [ ] Multi-account rotation for LinkedIn
- [ ] Production deployment guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the [ethical guidelines](ethics/ETHICAL_GUIDELINES.md)
3. Run the test suite: `python tests/test_scrapers.py`
4. Test API connections: `python test_apis.py`

---

*Last Updated: December 3, 2025*
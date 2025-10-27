# Social Media Scraping v2

A robust, ethical social media data collection tool that scrapes public data from multiple platforms for sentiment analysis, trend tracking, and market research purposes.

## 🚀 Features

- **Multi-Platform Support**: Twitter/X, Reddit (LinkedIn, Instagram, YouTube coming in Week 2)
- **Ethical Scraping**: Rate limiting, robots.txt compliance, public data only
- **Robust Storage**: MongoDB with duplicate detection and indexing
- **API Access**: RESTful API for querying scraped data
- **Rate Limiting**: Built-in protection against API abuse
- **Data Export**: CSV and JSON export capabilities

## 🛠 Tech Stack

- **Backend**: Python 3.10+
- **APIs**: Twitter API v2, Reddit API (PRAW)
- **Database**: MongoDB (Atlas)
- **Data Processing**: Pandas, NumPy
- **Environment**: python-dotenv

## 📁 Project Structure

```
social-media-scraping-v2/
├── src/
│   ├── scrapers/
│   │   ├── twitter_scraper.py    # Twitter API integration
│   │   ├── reddit_scraper.py     # Reddit PRAW integration
│   │   └── base_scraper.py       # Base scraper class
│   ├── storage/
│   │   └── db.py                 # MongoDB data storage
│   ├── utils/
│   │   └── rate_limiter.py       # API rate limiting
│   └── main.py                   # Main application entry
├── tests/
│   └── test_scrapers.py          # Unit tests
├── ethics/
│   └── ETHICAL_GUIDELINES.md     # Ethical scraping guidelines
├── data/                         # Local data storage
├── requirements.txt              # Python dependencies
└── .env                         # Environment variables
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

Create a `.env` file with your API credentials:

```env
# Twitter API (get from https://developer.twitter.com)
TWITTER_BEARER_TOKEN="your_twitter_bearer_token"

# Reddit API (get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID="your_reddit_client_id"
REDDIT_CLIENT_SECRET="your_reddit_client_secret"
REDDIT_USER_AGENT="SocialMediaScraper/1.0"

# MongoDB (Atlas or local)
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
```

### 3. Usage

#### Basic Scraping

```python
from src.scrapers.reddit_scraper import RedditScraper
from src.scrapers.twitter_scraper import TwitterScraper
from src.storage.db import DataStore

# Initialize components
reddit = RedditScraper()
twitter = TwitterScraper()
store = DataStore()

# Scrape Reddit
posts = reddit.search_subreddits("Python programming", limit=10)
for post in posts:
    store.insert_post({
        "id": post["id"],
        "platform": "reddit",
        "title": post["title"],
        "content": post["text"],
        "author": post["author"],
        "url": post["url"],
        "metrics": {"score": post["score"]},
        "created_at": post["created_at"]
    })

# Scrape Twitter
tweets = twitter.search_tweets("Python", max_results=10)
for tweet in tweets:
    store.insert_post({
        "id": tweet["id"],
        "platform": "twitter",
        "content": tweet["text"],
        "metrics": tweet.get("public_metrics", {}),
        "created_at": tweet["created_at"]
    })
```

#### Run Main Script

```bash
python src/main.py
```

### 4. Testing

```bash
# Run all tests
python tests/test_scrapers.py

# Test API connections
python test_apis.py
```

## 📊 Data Schema

### Post Document Structure

```json
{
  "id": "unique_post_id",
  "platform": "reddit|twitter|linkedin|instagram|youtube",
  "title": "Post title (if applicable)",
  "content": "Full post content/text",
  "author": "username_or_id",
  "source_url": "original_post_url",
  "engagement_metrics": {
    "score": 100,
    "likes": 50,
    "shares": 25,
    "comments": 10
  },
  "created_at": "2025-10-27T12:00:00Z",
  "scraped_at": "2025-10-27T12:05:00Z"
}
```

## 🔧 API Reference

### RedditScraper

```python
scraper = RedditScraper()

# Search across all subreddits
posts = scraper.search_subreddits("keyword", limit=100)

# Get posts from specific subreddit
posts = scraper.get_subreddit_posts("python", limit=50)
```

### TwitterScraper

```python
scraper = TwitterScraper()

# Search recent tweets
tweets = scraper.search_tweets("keyword", max_results=100)
```

### DataStore

```python
store = DataStore()

# Insert post (with duplicate detection)
success = store.insert_post(post_data)

# Search stored posts
results = store.search_posts("keyword", limit=100)

# Filter by platform
results = store.filter_by_platform("reddit", limit=100)

# Get statistics
stats = store.get_stats()
```

## 🛡️ Ethical Guidelines

This tool follows strict ethical guidelines:

- **Public Data Only**: Only scrapes publicly available content
- **Rate Limiting**: Respects platform API limits and terms of service
- **No Personal Data**: Avoids collecting sensitive personal information
- **Robots.txt Compliance**: Respects website scraping preferences
- **Data Anonymization**: Options to anonymize user data

See [ETHICAL_GUIDELINES.md](ethics/ETHICAL_GUIDELINES.md) for full details.

## 🔍 Troubleshooting

### Twitter API Issues

- **401 Unauthorized**: Check your bearer token
- **429 Rate Limited**: Wait for rate limit reset (15 minutes)
- **403 Forbidden**: Your access level may not support search endpoints

### Reddit API Issues

- **Missing Credentials**: Ensure all Reddit environment variables are set
- **Rate Limiting**: Reddit allows ~100 requests per minute

### MongoDB Issues

- **Connection Failed**: Check your MongoDB URI and network access
- **Authentication Failed**: Verify username/password in connection string

## 📈 Development Roadmap

### Week 1 ✅ (Completed)
- [x] Repository setup
- [x] Twitter scraper (official API)
- [x] Reddit scraper (PRAW)
- [x] Data storage system (MongoDB)
- [x] Basic testing
- [x] Rate limiting

### Week 2 (Coming Soon)
- [ ] LinkedIn scraper (public posts)
- [ ] Instagram scraper (public profiles)
- [ ] Advanced rate limiting
- [ ] Data processing and cleaning
- [ ] Search and filter enhancements

### Week 3 (Planned)
- [ ] RESTful API
- [ ] Export functionality
- [ ] Webhook system
- [ ] Performance optimization

### Week 4 (Planned)
- [ ] Security review
- [ ] Documentation completion
- [ ] Demo creation
- [ ] Production deployment

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

*Last Updated: October 27, 2025*
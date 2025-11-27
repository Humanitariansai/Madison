# Streamlit Deployment Guide

## Deploy Streamlit UI on Streamlit Community Cloud (FREE)

### Step 1: Prepare the Repository

Your Streamlit app is already ready at:
`Social-Media-Scraping/social-media-scraping-v2/app_combined.py`

### Step 2: Create packages.txt (for LinkedIn Selenium)

This file tells Streamlit Cloud to install Chrome.

### Step 3: Deploy on Streamlit Cloud

1. **Go to**: https://share.streamlit.io
2. **Sign in** with email (or GitHub if you have access)
3. Click **"New app"**
4. **Repository**: `Humanitariansai/Madison`
5. **Branch**: `main`
6. **Main file path**: `Social-Media-Scraping/social-media-scraping-v2/app_combined.py`
7. Click **"Advanced settings"**

### Step 4: Add Secrets

In Advanced settings → Secrets, paste:

```toml
MONGODB_URI = "mongodb+srv://zlatanised:Zlatan11@humanitariansai.vwerb9i.mongodb.net/"
REDDIT_CLIENT_ID = "Sy8xB1l2WJEbnrSjpNn3CA"
REDDIT_CLIENT_SECRET = "BIABisGHQtId4CMT1jVueQCgYrKDYg"
REDDIT_USER_AGENT = "SocialMediaScraper/1.0"
LINKEDIN_USERNAME = "ctcmerj.j575u@simplelogin.co"
LINKEDIN_PASSWORD = "Zlatanlinkedin@11"
```

### Step 5: Deploy

Click **"Deploy!"**

Wait 5-10 minutes for deployment.

### Your Public URL

You'll get a URL like:
`https://your-app.streamlit.app`

Anyone can access it and scrape!

---

## Alternative: Deploy Streamlit on Render

If Streamlit Cloud doesn't work with LinkedIn Selenium:

### Create Dockerfile.streamlit

```dockerfile
FROM python:3.11-slim

# Install Chrome
RUN apt-get update && apt-get install -y \
    wget ca-certificates \
    && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8501

CMD ["streamlit", "run", "app_combined.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Then deploy as a separate Render web service.

---

## Notes

- **LinkedIn Selenium**: May be blocked on cloud IPs
- **Free tier**: Cold starts after inactivity
- **Public access**: Anyone with URL can use it
- **No authentication**: Consider adding password protection if needed

## Testing

After deployment, test:
1. Search for a keyword on Reddit
2. Search for content on LinkedIn
3. Export to CSV
4. Save to database

Your users can now scrape directly from the web UI!

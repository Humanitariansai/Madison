# Quick Deploy: Streamlit UI

## 🚀 Deploy in 5 Minutes

### Step 1: Push Changes
```bash
cd /Users/zlatan/Desktop/Work/Madison
git add .
git commit -m "Add Streamlit deployment config"
git push origin main
```

### Step 2: Go to Streamlit Cloud
1. Visit: https://share.streamlit.io
2. Sign in with email
3. Click **"New app"**

### Step 3: Configure
- **Repository**: `Humanitariansai/Madison`
- **Branch**: `main`
- **Main file**: `Social-Media-Scraping/social-media-scraping-v2/app_combined.py`

### Step 4: Add Secrets
Click **"Advanced settings"** → **Secrets**, paste:

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

Wait 5-10 minutes. You'll get a public URL like:
`https://your-app-name.streamlit.app`

## ✅ Done!

Share this URL with anyone - they can:
- Search Reddit posts
- Search LinkedIn content
- Export to CSV
- Save to your MongoDB

## 📝 Files Added
- `packages.txt` - Installs Chromium for LinkedIn
- `STREAMLIT_DEPLOY.md` - Full deployment guide
- Updated LinkedIn scraper for Streamlit Cloud compatibility

## ⚠️ Notes
- LinkedIn may still block cloud IPs
- Free tier includes cold starts
- No authentication by default (public access)

## Next: Add Authentication (Optional)
If you want to restrict access, add password protection:
```python
import streamlit as st

password = st.text_input("Enter password", type="password")
if password != "your_secret_password":
    st.stop()
```

Push and you're live! 🎉

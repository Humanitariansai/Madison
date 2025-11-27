# Render Deployment Guide (Without Direct GitHub Access)

## Prerequisites
- Public GitHub repo: https://github.com/Humanitariansai/Madison
- MongoDB Atlas account (free tier)
- Reddit API credentials
- LinkedIn credentials

## Step-by-Step Deployment

### 1. Prepare MongoDB (5 minutes)

1. Go to https://mongodb.com/cloud/atlas
2. Sign up / Login
3. Create Free Cluster (M0 - 512MB)
4. **Database Access**: Create user with password
5. **Network Access**: Add `0.0.0.0/0` (allow from anywhere)
6. **Connect**: Get connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/social_media_db
   ```

### 2. Deploy on Render (10 minutes)

#### Option A: Using Public Repo URL (Recommended)

1. **Go to**: https://render.com
2. **Sign up** with email (no GitHub connection needed)
3. Click **"New +"** → **"Web Service"**
4. Select **"Public Git repository"**
5. **Paste URL**: `https://github.com/Humanitariansai/Madison`
6. Click **"Continue"**

**Configuration:**
- **Name**: `social-media-scraper` (or any name)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: `Social-Media-Scraping/social-media-scraping-v2`
- **Environment**: `Docker`
- **Plan**: `Free`

**Advanced Settings:**
- **Docker Build Context Path**: `Social-Media-Scraping/social-media-scraping-v2`
- **Dockerfile Path**: `./Dockerfile`
- **Health Check Path**: `/health`

7. **Add Environment Variables** (click "Add Environment Variable"):
   ```
   MONGODB_URI = mongodb+srv://user:pass@cluster.mongodb.net/social_media_db
   REDDIT_CLIENT_ID = your_reddit_client_id
   REDDIT_CLIENT_SECRET = your_reddit_secret
   REDDIT_USER_AGENT = Mozilla/5.0 (compatible; RedditScraper/1.0)
   LINKEDIN_USERNAME = your_linkedin_email
   LINKEDIN_PASSWORD = your_linkedin_password
   ```

8. Click **"Create Web Service"**

**Wait 5-10 minutes** for build to complete.

#### Option B: If Subdirectory Doesn't Work

If Render can't handle subdirectory from public repo:

1. **Create separate branch** with just the scraper code:
   ```bash
   cd /Users/zlatan/Desktop/Work/Madison
   git checkout -b deploy-scraper
   git filter-branch --subdirectory-filter Social-Media-Scraping/social-media-scraping-v2 HEAD
   git push origin deploy-scraper
   ```

2. Then in Render, use:
   - **Root Directory**: `/` (empty)
   - **Branch**: `deploy-scraper`

### 3. Test Deployment

Once deployed, you'll get a URL like: `https://social-media-scraper-xyz.onrender.com`

**Test endpoints:**
```bash
# Health check
curl https://your-app.onrender.com/health

# Get stats
curl https://your-app.onrender.com/stats

# Get posts
curl https://your-app.onrender.com/posts

# API docs (in browser)
https://your-app.onrender.com/docs
```

### 4. Deploy Streamlit UI (Optional)

**On Streamlit Cloud:**
1. Go to https://streamlit.io/cloud
2. Sign up with email
3. **New app** → Use public repo
4. **Repository**: `Humanitariansai/Madison`
5. **Branch**: `main`
6. **Main file path**: `Social-Media-Scraping/social-media-scraping-v2/app_combined.py`
7. **Python version**: 3.11

**Add Secrets** (Settings → Secrets):
```toml
MONGODB_URI = "mongodb+srv://..."
REDDIT_CLIENT_ID = "..."
REDDIT_CLIENT_SECRET = "..."
REDDIT_USER_AGENT = "..."
LINKEDIN_USERNAME = "..."
LINKEDIN_PASSWORD = "..."
```

8. Click **Deploy**

### 5. Manual Deploy Updates (Without Auto-Deploy)

Since Render isn't connected to your GitHub:

**Method 1: Manual Trigger**
1. Go to Render Dashboard
2. Click your service
3. Click **"Manual Deploy"** → Select branch
4. Click **"Deploy"**

**Method 2: Deploy Hook**
1. In Render: Settings → Deploy Hook
2. Copy the webhook URL
3. Trigger deploys:
   ```bash
   curl -X POST https://api.render.com/deploy/srv-xxxxx?key=xxxxx
   ```

**Method 3: GitHub Actions** (if you have repo access)
Add to `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Render
on:
  push:
    branches: [main]
    paths:
      - 'Social-Media-Scraping/social-media-scraping-v2/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy
        run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

## Troubleshooting

### Build Fails
- Check logs in Render dashboard
- Verify Dockerfile paths are correct
- Ensure requirements.txt includes fastapi, uvicorn, pydantic

### LinkedIn Scraper Fails
- LinkedIn may block datacenter IPs
- Add retry logic or use scheduled scraping
- Consider disabling LinkedIn for initial deployment

### Cold Starts
- Free tier sleeps after 15min inactivity
- First request takes 30-60 seconds
- Upgrade to paid ($7/mo) for always-on

### Database Connection Fails
- Check MongoDB Atlas whitelist includes `0.0.0.0/0`
- Verify connection string format
- Test locally first

### Port Issues
- Render expects app on port from `$PORT` env var
- Dockerfile uses: `--port 8000` but Render overrides this
- Our Dockerfile is correct (uses 8000)

## Cost Breakdown

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Render | 750 hours/month | Cold starts after 15min |
| MongoDB Atlas | 512MB storage | Enough for 10k+ posts |
| Streamlit Cloud | Unlimited | UI only |
| **Total** | **$0/month** | |

## Next Steps After Deployment

1. **Test all endpoints**: Use Swagger docs at `/docs`
2. **Run initial scrape**: Use Streamlit UI or API
3. **Monitor performance**: Check Render logs
4. **Set up monitoring**: Use UptimeRobot (free) to ping every 5min
5. **Add domain** (optional): Connect custom domain in Render settings

## Getting Deploy URL

After deployment completes:
- Render assigns URL: `https://your-app-name.onrender.com`
- Copy this URL
- Update Streamlit app if needed to point to this API

## Support

If deployment fails:
1. Check Render logs (Dashboard → Logs)
2. Verify all env vars are set
3. Test locally: `docker build -t scraper . && docker run -p 8000:8000 scraper`
4. Contact me with error logs

---

**Total Setup Time: 15-20 minutes**
**Monthly Cost: $0**

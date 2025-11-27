# Pre-Deployment Checklist

## ✅ Files Ready
- [x] Dockerfile (with Chrome for LinkedIn)
- [x] render.yaml (configuration)
- [x] requirements.txt (updated with FastAPI)
- [x] API health check endpoints (/ and /health)
- [x] LinkedIn headless mode enabled

## 📋 Before You Deploy

### 1. Push Latest Changes
```bash
cd /Users/zlatan/Desktop/Work/Madison
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Set Up MongoDB Atlas (5 min)
- [ ] Create account: https://mongodb.com/cloud/atlas
- [ ] Create free M0 cluster
- [ ] Create database user + password
- [ ] Whitelist IP: 0.0.0.0/0
- [ ] Get connection string

### 3. Have Reddit Credentials Ready
- [ ] REDDIT_CLIENT_ID
- [ ] REDDIT_CLIENT_SECRET
- [ ] REDDIT_USER_AGENT

### 4. Have LinkedIn Credentials Ready
- [ ] LINKEDIN_USERNAME (email)
- [ ] LINKEDIN_PASSWORD

## 🚀 Deployment Steps

Follow: `RENDER_DEPLOY.md`

**Quick Summary:**
1. Go to https://render.com
2. New Web Service → Public Git Repository
3. URL: `https://github.com/Humanitariansai/Madison`
4. Root Directory: `Social-Media-Scraping/social-media-scraping-v2`
5. Environment: Docker
6. Add all env variables
7. Deploy!

## 🧪 After Deployment

Test these URLs (replace with your Render URL):
```bash
# Health check
curl https://your-app.onrender.com/health

# Stats
curl https://your-app.onrender.com/stats

# API docs
https://your-app.onrender.com/docs
```

## ⚠️ Known Issues

**LinkedIn Scraping:**
- May fail due to IP blocking
- Headless Chrome sometimes detected
- Consider scheduled scraping vs real-time

**Free Tier Limits:**
- Cold starts after 15 min (30-60s delay)
- 750 hours/month (enough for 24/7)
- 512MB RAM (sufficient for your use case)

## 💡 Tips

1. **Test locally first:**
   ```bash
   docker build -t scraper .
   docker run -p 8000:8000 --env-file .env scraper
   ```

2. **Manual deploys:**
   - Render won't auto-deploy without GitHub OAuth
   - Use "Manual Deploy" button after each git push
   - Or set up deploy webhook

3. **Monitor cold starts:**
   - Use UptimeRobot.com (free) to ping every 10min
   - Keeps app warm and provides uptime monitoring

## 📝 Environment Variables Format

Copy this template:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/social_media_db
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=Mozilla/5.0 (compatible; RedditScraper/1.0)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password_here
```

## ✨ Ready to Deploy!

All files are configured. Follow `RENDER_DEPLOY.md` for detailed steps.

**Estimated time:** 15-20 minutes
**Cost:** $0/month

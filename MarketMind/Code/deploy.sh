#!/bin/bash

# MarketMind Deployment Script
echo "🚀 MarketMind Deployment Script"
echo "================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Initializing..."
    git init
    git add .
    git commit -m "Initial MarketMind commit"
    echo "✅ Git repository initialized"
fi

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "❌ No remote repository found."
    echo "Please create a GitHub repository and add it as origin:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    exit 1
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Update MarketMind for deployment"
git push origin main

echo "✅ Code pushed to GitHub!"
echo ""
echo "🎯 Next Steps:"
echo "1. Go to https://share.streamlit.io"
echo "2. Sign in with GitHub"
echo "3. Click 'New app'"
echo "4. Select your repository"
echo "5. Set main file path to: app.py"
echo "6. Add your API keys in the secrets section:"
echo "   OPENAI_API_KEY = your_openai_key"
echo "   SERPER_API_KEY = your_serper_key"
echo "   FIRECRAWL_API_KEY = your_firecrawl_key"
echo "7. Click 'Deploy'"
echo ""
echo "🌐 Your app will be available at: https://your-app-name.streamlit.app"
echo ""
echo "📧 Share this URL with your stakeholders - no setup required!" 
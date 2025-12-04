#!/bin/bash
# Update and restart EC2 LinkedIn Scraper
# Usage: bash update_service.sh

echo "=========================================="
echo "LinkedIn Scraper Service Update"
echo "=========================================="

# Pull latest code
echo "📂 Pulling latest code from repository..."
cd ~/Madison
git pull origin main

# Go to app directory
cd ~/Madison/Social-Media-Scraping/social-media-scraping-v2

# Activate venv and install dependencies
echo ""
echo "📚 Installing/updating dependencies..."
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart service
echo ""
echo "🔄 Restarting service..."
sudo systemctl restart linkedin-scraper

# Wait for service to start
sleep 3

# Check status
echo ""
echo "✅ Service Status:"
sudo systemctl status linkedin-scraper

echo ""
echo "📊 Testing endpoint..."
curl -s http://localhost/health | python3 -m json.tool || echo "⚠️ Service still starting..."

echo ""
echo "=========================================="
echo "✅ Update Complete!"
echo "=========================================="
echo ""
echo "View logs with: sudo journalctl -u linkedin-scraper -f"

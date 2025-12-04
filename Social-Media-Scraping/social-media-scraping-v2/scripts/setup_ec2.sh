#!/bin/bash
# EC2 Setup Script - Run this on your new Ubuntu EC2 instance
# Usage: bash setup_ec2.sh

set -e

echo "=========================================="
echo "LinkedIn Scraper EC2 Setup"
echo "=========================================="

# Step 1: Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Chrome and dependencies
echo "🌐 Installing Chromium and dependencies..."
sudo apt install -y chromium-browser chromium-driver

# Step 3: Install Python and build tools
echo "🐍 Installing Python and build tools..."
sudo apt install -y python3-pip python3-venv git libssl-dev libffi-dev build-essential

# Verify installations
echo ""
echo "✅ Verifying installations..."
echo "Chromium version:"
chromium-browser --version
echo "ChromeDriver version:"
chromedriver --version
echo "Python version:"
python3 --version

# Step 4: Clone repository
echo ""
echo "📂 Cloning repository..."
cd ~
if [ ! -d "Madison" ]; then
    git clone https://github.com/Humanitariansai/Madison.git
else
    echo "Repository already exists, pulling latest..."
    cd Madison
    git pull origin main
    cd ~
fi

# Step 5: Setup virtual environment
echo ""
echo "🔧 Setting up Python environment..."
cd ~/Madison/Social-Media-Scraping/social-media-scraping-v2
python3 -m venv venv
source venv/bin/activate

# Step 6: Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Step 7: Create .env file
echo ""
echo "🔐 Creating .env file..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
LINKEDIN_LOW_MEM=false
EOF
    echo "⚠️  .env file created. PLEASE UPDATE WITH YOUR CREDENTIALS:"
    echo "   nano .env"
else
    echo ".env file already exists"
fi

# Step 8: Install nginx
echo ""
echo "🔌 Installing nginx..."
sudo apt install -y nginx

# Step 9: Configure nginx
echo "⚙️  Configuring nginx..."
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
upstream linkedin_scraper {
    server 127.0.0.1:9000;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    proxy_buffer_size 128k;
    proxy_buffers 4 256k;

    location / {
        proxy_pass http://linkedin_scraper;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

sudo systemctl restart nginx
sudo systemctl enable nginx

# Step 10: Create systemd service
echo ""
echo "🚀 Creating systemd service..."
sudo tee /etc/systemd/system/linkedin-scraper.service > /dev/null << EOF
[Unit]
Description=LinkedIn Scraper FastAPI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Madison/Social-Media-Scraping/social-media-scraping-v2
Environment="PATH=/home/ubuntu/Madison/Social-Media-Scraping/social-media-scraping-v2/venv/bin"
ExecStart=/home/ubuntu/Madison/Social-Media-Scraping/social-media-scraping-v2/venv/bin/python local_linkedin_runner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable linkedin-scraper

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo "1. Update credentials: nano .env"
echo "2. Start service: sudo systemctl start linkedin-scraper"
echo "3. Check status: sudo systemctl status linkedin-scraper"
echo "4. Test endpoint: curl http://localhost/health"
echo ""
echo "📊 To view logs:"
echo "   sudo journalctl -u linkedin-scraper -f"
echo ""
echo "🌐 Access from your computer:"
echo "   http://<your-ec2-ip>/health"
echo ""

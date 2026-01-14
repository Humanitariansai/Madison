#!/bin/bash
# Quick Start Script - Complete deployment in one command
# Usage: ./deploy/quick-start.sh PROJECT_ID REGION

set -e

PROJECT_ID=${1}
REGION=${2:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: Project ID is required"
    echo "Usage: ./deploy/quick-start.sh PROJECT_ID [REGION]"
    exit 1
fi

echo "🚀 Quick Start: Deploying Survey Analysis to Google Cloud"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Step 1: Setup GCP resources
echo "📦 Step 1: Setting up GCP resources..."
chmod +x deploy/setup-gcp.sh
./deploy/setup-gcp.sh $PROJECT_ID $REGION

# Step 2: Deploy application
echo ""
echo "🚀 Step 2: Deploying application..."
chmod +x deploy/deploy.sh
./deploy/deploy.sh $PROJECT_ID $REGION

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Get your service URLs:"
echo "   gcloud run services list --region $REGION"
echo ""


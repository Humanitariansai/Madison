#!/bin/bash
# Deployment script for Survey Analysis Application
# This script builds and deploys the application to Google Cloud Run

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}

echo "🚀 Deploying Survey Analysis Application to Google Cloud"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID

# Get secrets for environment variables
echo "🔐 Retrieving secrets..."
JWT_SECRET=$(gcloud secrets versions access latest --secret="jwt-secret")
DB_PASSWORD=$(gcloud secrets versions access latest --secret="db-password")
DATABASE_URL=$(gcloud secrets versions access latest --secret="database-url")
REDIS_URL=$(gcloud secrets versions access latest --secret="redis-url")

# Get Cloud SQL connection name
SQL_CONNECTION_NAME=$(gcloud sql instances describe survey-analysis-db --format="value(connectionName)")

# Build and deploy backend
echo "🔨 Building backend..."
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/survey-analysis-backend

echo "🚀 Deploying backend to Cloud Run..."
gcloud run deploy survey-analysis-backend \
    --image gcr.io/$PROJECT_ID/survey-analysis-backend \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --service-account survey-analysis-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --add-cloudsql-instances $SQL_CONNECTION_NAME \
    --set-env-vars "PORT=8080,DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,SECRET_KEY=$JWT_SECRET,ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=30" \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest"

BACKEND_URL=$(gcloud run services describe survey-analysis-backend --region $REGION --format="value(status.url)")

echo "✅ Backend deployed at: $BACKEND_URL"

# Build and deploy frontend
echo "🔨 Building frontend..."
cd ../frontend

# Update API URL in .env file
echo "VITE_API_BASE_URL=$BACKEND_URL" > .env.production

gcloud builds submit --tag gcr.io/$PROJECT_ID/survey-analysis-frontend

echo "🚀 Deploying frontend to Cloud Run..."
gcloud run deploy survey-analysis-frontend \
    --image gcr.io/$PROJECT_ID/survey-analysis-frontend \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --port 80

FRONTEND_URL=$(gcloud run services describe survey-analysis-frontend --region $REGION --format="value(status.url)")

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: $BACKEND_URL"
echo ""
echo "📝 Update your frontend .env.production with:"
echo "   VITE_API_BASE_URL=$BACKEND_URL"
echo ""


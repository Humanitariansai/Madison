#!/bin/bash
# Script to update Cloud Run environment variables

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}

echo "🔄 Updating Cloud Run environment variables..."

# Get secrets
JWT_SECRET=$(gcloud secrets versions access latest --secret="jwt-secret")
DATABASE_URL=$(gcloud secrets versions access latest --secret="database-url")
REDIS_URL=$(gcloud secrets versions access latest --secret="redis-url")

# Get SQL connection name
SQL_CONNECTION_NAME=$(gcloud sql instances describe survey-analysis-db --format="value(connectionName)")

# Update backend service
gcloud run services update survey-analysis-backend \
    --region $REGION \
    --update-env-vars "PORT=8080,DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,SECRET_KEY=$JWT_SECRET,ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=30" \
    --update-secrets "OPENAI_API_KEY=openai-api-key:latest" \
    --add-cloudsql-instances $SQL_CONNECTION_NAME

echo "✅ Environment variables updated!"


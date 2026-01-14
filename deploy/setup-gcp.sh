#!/bin/bash
# Google Cloud Platform Setup Script
# This script sets up all necessary GCP resources for the survey analysis application

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
ZONE=${3:-"us-central1-a"}

echo "🚀 Setting up GCP resources for Survey Analysis Application"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Zone: $ZONE"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📦 Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    storage-component.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com

# Create Cloud SQL instance (PostgreSQL)
echo "🗄️  Creating Cloud SQL PostgreSQL instance..."
gcloud sql instances create survey-analysis-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=$(openssl rand -base64 32) \
    --storage-type=SSD \
    --storage-size=20GB \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4

# Create database
echo "📊 Creating database..."
gcloud sql databases create survey_analysis --instance=survey-analysis-db

# Create database user
DB_USER="survey_user"
DB_PASSWORD=$(openssl rand -base64 32)
echo "👤 Creating database user..."
gcloud sql users create $DB_USER \
    --instance=survey-analysis-db \
    --password=$DB_PASSWORD

echo "✅ Database credentials:"
echo "   User: $DB_USER"
echo "   Password: $DB_PASSWORD"
echo "   ⚠️  Save these credentials securely!"

# Create Redis instance (Memorystore)
echo "🔴 Creating Redis instance..."
gcloud redis instances create survey-analysis-redis \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_7_0 \
    --tier=basic

# Get Redis host
REDIS_HOST=$(gcloud redis instances describe survey-analysis-redis --region=$REGION --format="value(host)")

# Create Cloud Storage bucket for file uploads
echo "📦 Creating Cloud Storage bucket..."
BUCKET_NAME="${PROJECT_ID}-survey-analysis-files"
gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME || echo "Bucket may already exist"

# Set bucket CORS for frontend access
echo "🌐 Setting up CORS for storage bucket..."
cat > /tmp/cors.json <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "POST", "PUT", "DELETE", "HEAD"],
    "responseHeader": ["Content-Type", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set /tmp/cors.json gs://$BUCKET_NAME

# Create secrets in Secret Manager
echo "🔐 Creating secrets in Secret Manager..."

# Generate JWT secret
JWT_SECRET=$(openssl rand -base64 32)
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret --data-file=- --replication-policy="automatic" || \
    echo -n "$JWT_SECRET" | gcloud secrets versions add jwt-secret --data-file=-

# Store database password
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=- --replication-policy="automatic" || \
    echo -n "$DB_PASSWORD" | gcloud secrets versions add db-password --data-file=-

# Store database connection string
DB_CONNECTION_STRING="postgresql://$DB_USER:$DB_PASSWORD@/survey_analysis?host=/cloudsql/$PROJECT_ID:$REGION:survey-analysis-db"
echo -n "$DB_CONNECTION_STRING" | gcloud secrets create database-url --data-file=- --replication-policy="automatic" || \
    echo -n "$DB_CONNECTION_STRING" | gcloud secrets versions add database-url --data-file=-

# Store Redis URL
echo -n "redis://$REDIS_HOST:6379/0" | gcloud secrets create redis-url --data-file=- --replication-policy="automatic" || \
    echo -n "redis://$REDIS_HOST:6379/0" | gcloud secrets versions add redis-url --data-file=-

# Create service account for Cloud Run
echo "👤 Creating service account..."
gcloud iam service-accounts create survey-analysis-sa \
    --display-name="Survey Analysis Service Account" \
    --description="Service account for survey analysis Cloud Run services"

# Grant necessary permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:survey-analysis-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:survey-analysis-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:survey-analysis-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Grant Cloud Build permissions
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

echo ""
echo "✅ GCP setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update backend/.env with the following:"
echo "   DATABASE_URL=$DB_CONNECTION_STRING"
echo "   REDIS_URL=redis://$REDIS_HOST:6379/0"
echo "   SECRET_KEY=<from jwt-secret secret>"
echo ""
echo "2. Update frontend/.env with:"
echo "   VITE_API_BASE_URL=https://survey-analysis-backend-<hash>-uc.a.run.app"
echo ""
echo "3. Run: gcloud builds submit --config cloudbuild.yaml"
echo ""


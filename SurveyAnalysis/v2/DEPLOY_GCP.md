# Deploy to Google Cloud Platform - Step by Step Guide

## Prerequisites

### 1. Install Google Cloud SDK

**For Windows:**
1. Download from: https://cloud.google.com/sdk/docs/install
2. Run the installer
3. Restart your terminal/PowerShell

**Or use PowerShell:**
```powershell
# Download and install
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

**Verify installation:**
```powershell
gcloud --version
```

### 2. Create GCP Project

1. Go to: https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Enter project name: `survey-analysis-app`
4. Note your **Project ID** (e.g., `survey-analysis-app-123456`)

### 3. Enable Billing

1. Go to: https://console.cloud.google.com/billing
2. Link a billing account to your project
3. ⚠️ **Required** - GCP requires billing even for free tier

## Step 1: Login and Configure

```powershell
# Login to GCP (opens browser)
gcloud auth login

# Set your project (replace with your Project ID)
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config get-value project
```

## Step 2: Setup GCP Resources

**⚠️ IMPORTANT: If using the PowerShell script, skip to Step 3!**

**Option A: Using the setup script (Recommended)**

```powershell
# Make script executable (if needed)
# Navigate to project root
cd C:\Users\Owner\Downloads\survey_analysis

# Run setup script (replace YOUR_PROJECT_ID)
bash deploy/setup-gcp.sh YOUR_PROJECT_ID us-central1 us-central1-a
```

**Option B: Manual setup (if script doesn't work on Windows)**

```powershell
# Set variables
$PROJECT_ID = "YOUR_PROJECT_ID"
$REGION = "us-central1"

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create Cloud SQL PostgreSQL
gcloud sql instances create survey-analysis-db `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=$REGION `
    --root-password=ChangeThisPassword123! `
    --storage-type=SSD `
    --storage-size=20GB

# Create database
gcloud sql databases create survey_analysis --instance=survey-analysis-db

# Create database user
gcloud sql users create survey_user `
    --instance=survey-analysis-db `
    --password=ChangeThisPassword123!

# Create Redis instance
gcloud redis instances create survey-analysis-redis `
    --size=1 `
    --region=$REGION `
    --redis-version=redis_7_0 `
    --tier=basic

# Create Cloud Storage bucket
gsutil mb -p $PROJECT_ID -l $REGION gs://$PROJECT_ID-survey-analysis-files

# Create secrets
$JWT_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
echo $JWT_SECRET | gcloud secrets create jwt-secret --data-file=-

# Store database password
echo "ChangeThisPassword123!" | gcloud secrets create db-password --data-file=-

# Get connection details
$SQL_CONNECTION = gcloud sql instances describe survey-analysis-db --format="value(connectionName)"
$REDIS_HOST = gcloud redis instances describe survey-analysis-redis --region=$REGION --format="value(host)"

# Store connection strings
echo "postgresql://survey_user:ChangeThisPassword123!@/survey_analysis?host=/cloudsql/$SQL_CONNECTION" | gcloud secrets create database-url --data-file=-
echo "redis://$REDIS_HOST:6379/0" | gcloud secrets create redis-url --data-file=-
```

## Step 3: Add OpenAI API Key (Optional)

If you want to use AI features:

```powershell
echo "sk-your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-
```

## Step 4: Deploy Application

**Option A: Using deployment script**

```powershell
# Run deployment script
bash deploy/deploy.sh YOUR_PROJECT_ID us-central1
```

**Option B: Manual deployment**

### Deploy Backend

```powershell
cd backend

# Build Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/survey-analysis-backend

# Get secrets
$JWT_SECRET = gcloud secrets versions access latest --secret="jwt-secret"
$DATABASE_URL = gcloud secrets versions access latest --secret="database-url"
$REDIS_URL = gcloud secrets versions access latest --secret="redis-url"
$SQL_CONNECTION = gcloud sql instances describe survey-analysis-db --format="value(connectionName)"

# Deploy to Cloud Run
gcloud run deploy survey-analysis-backend `
    --image gcr.io/YOUR_PROJECT_ID/survey-analysis-backend `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars "PORT=8080,DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,SECRET_KEY=$JWT_SECRET" `
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest" `
    --add-cloudsql-instances $SQL_CONNECTION

# Get backend URL
$BACKEND_URL = gcloud run services describe survey-analysis-backend --region us-central1 --format="value(status.url)"
Write-Host "Backend URL: $BACKEND_URL"
```

### Deploy Frontend

```powershell
cd ..\frontend

# Update API URL
echo "VITE_API_BASE_URL=$BACKEND_URL" > .env.production

# Build Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/survey-analysis-frontend

# Deploy to Cloud Run
gcloud run deploy survey-analysis-frontend `
    --image gcr.io/YOUR_PROJECT_ID/survey-analysis-frontend `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --port 80

# Get frontend URL
$FRONTEND_URL = gcloud run services describe survey-analysis-frontend --region us-central1 --format="value(status.url)"
Write-Host "Frontend URL: $FRONTEND_URL"
```

## Step 5: Initialize Database

```powershell
cd ..\backend

# Connect to Cloud SQL and run migrations
# Option 1: Using Cloud SQL Proxy (recommended)
# Download: https://cloud.google.com/sql/docs/postgres/sql-proxy

# Option 2: Run migration script (if you have Cloud SQL Proxy set up)
python setup_database.py
```

## Step 6: Get Service URLs

```powershell
# List all services
gcloud run services list --region us-central1

# Get specific URLs
gcloud run services describe survey-analysis-backend --region us-central1 --format="value(status.url)"
gcloud run services describe survey-analysis-frontend --region us-central1 --format="value(status.url)"
```

## Quick Reference

### Important Commands

```powershell
# Check service status
gcloud run services list

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Update environment variables
gcloud run services update survey-analysis-backend --region us-central1 --update-env-vars "KEY=value"

# Redeploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/survey-analysis-backend
gcloud run deploy survey-analysis-backend --image gcr.io/YOUR_PROJECT_ID/survey-analysis-backend --region us-central1
```

### Cost Estimation (Minimal Resources)

- **Cloud Run Backend**: ~$5-10/month (512Mi, 1 CPU, max 3 instances)
- **Cloud Run Frontend**: ~$2-5/month (256Mi, 1 CPU, max 2 instances)
- **Cloud SQL**: ~$7/month (db-f1-micro, 10GB storage)
- **Memorystore**: ~$30/month (1GB Redis - basic tier)
- **Cloud Storage**: ~$1-2/month (minimal usage)
- **Total**: ~$45-55/month

**Note:** Redis is the biggest cost. If you want to reduce further, you can:
- Remove Redis and use in-memory caching (not recommended for production)
- Use Cloud SQL's built-in connection pooling instead

## Destroy Resources (Cleanup)

To delete all resources and stop billing:

```powershell
# Interactive mode (asks for confirmation)
.\deploy\destroy-gcp.ps1 -ProjectId "YOUR_PROJECT_ID" -Region "us-central1"

# Force mode (no confirmation - use with caution!)
.\deploy\destroy-gcp.ps1 -ProjectId "YOUR_PROJECT_ID" -Region "us-central1" -Force
```

**This will delete:**
- ✅ Cloud Run services (frontend & backend)
- ✅ Cloud SQL instance and database
- ✅ Redis instance
- ✅ Cloud Storage bucket
- ✅ Secrets
- ✅ Service account
- ✅ Container images

**Note:** APIs will remain enabled. To disable them:
```powershell
gcloud services disable cloudbuild.googleapis.com,run.googleapis.com,sqladmin.googleapis.com,redis.googleapis.com,storage-component.googleapis.com,secretmanager.googleapis.com,containerregistry.googleapis.com
```

## Troubleshooting

### gcloud not found
- Install Google Cloud SDK
- Restart terminal
- Verify: `gcloud --version`

### Permission errors
- Enable billing
- Check IAM roles (need Owner/Editor)
- Verify APIs are enabled

### Build failures
- Check Dockerfile syntax
- Verify all files are present
- Review Cloud Build logs

### Database connection issues
- Verify Cloud SQL instance is running
- Check connection name format
- Verify service account permissions

## Next Steps

1. ✅ Test the deployed application
2. ✅ Set up custom domain (optional)
3. ✅ Configure monitoring
4. ✅ Set up CI/CD pipeline

---

**Your application will be live at the Cloud Run URLs!** 🚀


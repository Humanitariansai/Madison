# PowerShell Deployment Script for Google Cloud Platform (MINIMAL RESOURCES)
# Usage: .\deploy\deploy-gcp-minimal.ps1 -ProjectId "your-project-id" -Region "us-central1"
# 
# This version uses minimal resources to reduce costs:
# - Cloud SQL: db-f1-micro, 10GB storage
# - Cloud Run Backend: 512Mi memory, 1 CPU, max 3 instances
# - Cloud Run Frontend: 256Mi memory, 1 CPU, max 2 instances
# - Redis: 1GB basic tier (can be removed if not needed)

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipRedis = $false
)

Write-Host "🚀 Deploying Survey Analysis Application to Google Cloud (MINIMAL RESOURCES)" -ForegroundColor Green
Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
if ($SkipRedis) {
    Write-Host "⚠️  Redis will be SKIPPED (using in-memory cache only)" -ForegroundColor Yellow
}
Write-Host ""

# Set the project
Write-Host "📋 Setting project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Check if gcloud is installed
$gcloudPath = "C:\Users\Owner\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $gcloudPath)) {
    $gcloudCmd = Get-Command gcloud -ErrorAction SilentlyContinue
    if ($gcloudCmd) {
        $gcloudPath = $gcloudCmd.Source
    } else {
        Write-Host "❌ Error: gcloud CLI not found." -ForegroundColor Red
        exit 1
    }
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Set-Alias -Name gcloud -Value $gcloudPath -Scope Script
}

# Step 1: Setup GCP Resources
Write-Host "`n📦 Step 1: Setting up GCP resources (MINIMAL)..." -ForegroundColor Yellow

# Enable APIs
Write-Host "Enabling required APIs..." -ForegroundColor Gray
gcloud services enable cloudbuild.googleapis.com,run.googleapis.com,sqladmin.googleapis.com,storage-component.googleapis.com,secretmanager.googleapis.com,containerregistry.googleapis.com

if (-not $SkipRedis) {
    gcloud services enable redis.googleapis.com
}

# Create Cloud SQL instance (MINIMAL: db-f1-micro, 10GB)
Write-Host "Creating Cloud SQL PostgreSQL instance (MINIMAL)..." -ForegroundColor Gray
$dbPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
try {
    gcloud sql instances create survey-analysis-db `
        --database-version=POSTGRES_15 `
        --tier=db-f1-micro `
        --region=$Region `
        --root-password=$dbPassword `
        --storage-type=SSD `
        --storage-size=10GB
    Write-Host "✅ Cloud SQL instance created (db-f1-micro, 10GB)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Cloud SQL instance may already exist" -ForegroundColor Yellow
}

# Create database
Write-Host "Creating database..." -ForegroundColor Gray
gcloud sql databases create survey_analysis --instance=survey-analysis-db 2>$null

# Create database user
$dbUser = "survey_user"
$dbUserPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
Write-Host "Creating database user..." -ForegroundColor Gray
gcloud sql users create $dbUser --instance=survey-analysis-db --password=$dbUserPassword 2>$null

# Create Redis instance (OPTIONAL - can skip to save $30/month)
$redisHost = $null
$redisUrl = $null
if (-not $SkipRedis) {
    Write-Host "Creating Redis instance (MINIMAL: 1GB basic)..." -ForegroundColor Gray
    try {
        gcloud redis instances create survey-analysis-redis `
            --size=1 `
            --region=$Region `
            --redis-version=redis_7_0 `
            --tier=basic
        Write-Host "✅ Redis instance created (1GB basic)" -ForegroundColor Green
        $redisHost = gcloud redis instances describe survey-analysis-redis --region=$Region --format="value(host)"
        $redisUrl = "redis://$redisHost`:6379/0"
    } catch {
        Write-Host "⚠️  Redis instance may already exist" -ForegroundColor Yellow
        $redisHost = gcloud redis instances describe survey-analysis-redis --region=$Region --format="value(host)" 2>$null
        if ($redisHost) {
            $redisUrl = "redis://$redisHost`:6379/0"
        }
    }
} else {
    Write-Host "⏭️  Skipping Redis (using in-memory cache)" -ForegroundColor Yellow
    $redisUrl = "memory://"
}

# Get connection details
$sqlConnection = gcloud sql instances describe survey-analysis-db --format="value(connectionName)"

# Create Cloud Storage bucket
Write-Host "Creating Cloud Storage bucket..." -ForegroundColor Gray
$bucketName = "$ProjectId-survey-analysis-files"
gsutil mb -p $ProjectId -l $Region "gs://$bucketName" 2>$null

# Create secrets
Write-Host "Creating secrets..." -ForegroundColor Gray
$jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

echo $jwtSecret | gcloud secrets create jwt-secret --data-file=- 2>$null
echo $dbUserPassword | gcloud secrets create db-password --data-file=- 2>$null

$databaseUrl = "postgresql://$dbUser`:$dbUserPassword@/survey_analysis?host=/cloudsql/$sqlConnection"
echo $databaseUrl | gcloud secrets create database-url --data-file=- 2>$null

if ($redisUrl -and $redisUrl -ne "memory://") {
    echo $redisUrl | gcloud secrets create redis-url --data-file=- 2>$null
}

# Create service account
Write-Host "Creating service account..." -ForegroundColor Gray
gcloud iam service-accounts create survey-analysis-sa --display-name="Survey Analysis Service Account" 2>$null

# Grant permissions
Write-Host "Granting permissions..." -ForegroundColor Gray
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" --role="roles/cloudsql.client" 2>$null
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" 2>$null
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" --role="roles/storage.objectAdmin" 2>$null

Write-Host "✅ GCP resources setup complete!" -ForegroundColor Green

# Step 2: Deploy Backend (MINIMAL: 512Mi, 1 CPU, max 3 instances)
Write-Host "`n🔨 Step 2: Building and deploying backend (MINIMAL)..." -ForegroundColor Yellow
Set-Location backend

Write-Host "Building Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-backend"

Write-Host "Deploying to Cloud Run (512Mi, 1 CPU, max 3 instances)..." -ForegroundColor Gray
$jwtSecretValue = gcloud secrets versions access latest --secret="jwt-secret"
$databaseUrlValue = gcloud secrets versions access latest --secret="database-url"

if ($redisUrl -and $redisUrl -ne "memory://") {
    $redisUrlValue = gcloud secrets versions access latest --secret="redis-url"
} else {
    $redisUrlValue = "memory://"
}

gcloud run deploy survey-analysis-backend `
    --image "gcr.io/$ProjectId/survey-analysis-backend" `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 3 `
    --min-instances 0 `
    --service-account "survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" `
    --add-cloudsql-instances $sqlConnection `
    --set-env-vars "PORT=8080,DATABASE_URL=$databaseUrlValue,REDIS_URL=$redisUrlValue,SECRET_KEY=$jwtSecretValue,ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=30" `
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest"

$backendUrl = gcloud run services describe survey-analysis-backend --region $Region --format="value(status.url)"
Write-Host "✅ Backend deployed at: $backendUrl" -ForegroundColor Green

# Step 3: Deploy Frontend (MINIMAL: 256Mi, 1 CPU, max 2 instances)
Write-Host "`n🔨 Step 3: Building and deploying frontend (MINIMAL)..." -ForegroundColor Yellow
Set-Location ..\frontend

Write-Host "Updating API URL..." -ForegroundColor Gray
"VITE_API_BASE_URL=$backendUrl" | Out-File -FilePath .env.production -Encoding utf8

Write-Host "Building Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-frontend"

Write-Host "Deploying to Cloud Run (256Mi, 1 CPU, max 2 instances)..." -ForegroundColor Gray
gcloud run deploy survey-analysis-frontend `
    --image "gcr.io/$ProjectId/survey-analysis-frontend" `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 256Mi `
    --cpu 1 `
    --max-instances 2 `
    --min-instances 0 `
    --port 80

$frontendUrl = gcloud run services describe survey-analysis-frontend --region $Region --format="value(status.url)"

Write-Host "`n✅ Deployment complete (MINIMAL RESOURCES)!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host "🔧 Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "💰 Estimated Monthly Cost:" -ForegroundColor Yellow
if ($SkipRedis) {
    Write-Host "   ~$15-25/month (without Redis)" -ForegroundColor Green
} else {
    Write-Host "   ~$45-55/month (with Redis)" -ForegroundColor Green
}
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the application at: $frontendUrl"
Write-Host "2. Initialize database: python backend/setup_database.py"
Write-Host "3. View API docs: $backendUrl/docs"
Write-Host ""


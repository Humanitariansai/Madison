# PowerShell Script to Destroy GCP Resources
# Usage: .\deploy\destroy-gcp.ps1 -ProjectId "your-project-id" -Region "us-central1"
# 
# WARNING: This will DELETE all resources created by the deployment script!
# This includes:
# - Cloud Run services (frontend & backend)
# - Cloud SQL instance and database
# - Redis instance
# - Cloud Storage bucket
# - Secrets
# - Service account
#
# Use with caution!

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

Write-Host "⚠️  WARNING: This will DELETE all GCP resources!" -ForegroundColor Red
Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host ""

if (-not $Force) {
    $confirmation = Read-Host "Are you sure you want to delete all resources? Type 'yes' to confirm"
    if ($confirmation -ne "yes") {
        Write-Host "❌ Cancelled. No resources were deleted." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "🗑️  Starting resource deletion..." -ForegroundColor Yellow
Write-Host ""

# Set the project
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

# Step 1: Delete Cloud Run Services
Write-Host "🗑️  Step 1: Deleting Cloud Run services..." -ForegroundColor Yellow

Write-Host "Deleting backend service..." -ForegroundColor Gray
try {
    gcloud run services delete survey-analysis-backend --region $Region --quiet 2>$null
    Write-Host "✅ Backend service deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend service not found or already deleted" -ForegroundColor Yellow
}

Write-Host "Deleting frontend service..." -ForegroundColor Gray
try {
    gcloud run services delete survey-analysis-frontend --region $Region --quiet 2>$null
    Write-Host "✅ Frontend service deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Frontend service not found or already deleted" -ForegroundColor Yellow
}

# Step 2: Delete Cloud SQL Instance
Write-Host "`n🗑️  Step 2: Deleting Cloud SQL instance..." -ForegroundColor Yellow
Write-Host "⚠️  This will delete the database and all data!" -ForegroundColor Red
try {
    gcloud sql instances delete survey-analysis-db --quiet
    Write-Host "✅ Cloud SQL instance deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Cloud SQL instance not found or already deleted" -ForegroundColor Yellow
}

# Step 3: Delete Redis Instance
Write-Host "`n🗑️  Step 3: Deleting Redis instance..." -ForegroundColor Yellow
try {
    gcloud redis instances delete survey-analysis-redis --region $Region --quiet
    Write-Host "✅ Redis instance deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Redis instance not found or already deleted" -ForegroundColor Yellow
}

# Step 4: Delete Cloud Storage Bucket
Write-Host "`n🗑️  Step 4: Deleting Cloud Storage bucket..." -ForegroundColor Yellow
$bucketName = "$ProjectId-survey-analysis-files"
try {
    # Delete all objects first
    gsutil -m rm -r "gs://$bucketName/**" 2>$null
    # Delete the bucket
    gsutil rb "gs://$bucketName" 2>$null
    Write-Host "✅ Cloud Storage bucket deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Cloud Storage bucket not found or already deleted" -ForegroundColor Yellow
}

# Step 5: Delete Secrets
Write-Host "`n🗑️  Step 5: Deleting secrets..." -ForegroundColor Yellow

$secrets = @("jwt-secret", "db-password", "database-url", "redis-url", "openai-api-key")
foreach ($secret in $secrets) {
    try {
        gcloud secrets delete $secret --quiet 2>$null
        Write-Host "✅ Secret '$secret' deleted" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Secret '$secret' not found or already deleted" -ForegroundColor Yellow
    }
}

# Step 6: Delete Service Account
Write-Host "`n🗑️  Step 6: Deleting service account..." -ForegroundColor Yellow
try {
    gcloud iam service-accounts delete "survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" --quiet 2>$null
    Write-Host "✅ Service account deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Service account not found or already deleted" -ForegroundColor Yellow
}

# Step 7: Delete Container Images
Write-Host "`n🗑️  Step 7: Deleting container images..." -ForegroundColor Yellow
try {
    # Delete backend image
    gcloud container images delete "gcr.io/$ProjectId/survey-analysis-backend" --force-delete-tags --quiet 2>$null
    Write-Host "✅ Backend image deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend image not found or already deleted" -ForegroundColor Yellow
}

try {
    # Delete frontend image
    gcloud container images delete "gcr.io/$ProjectId/survey-analysis-frontend" --force-delete-tags --quiet 2>$null
    Write-Host "✅ Frontend image deleted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Frontend image not found or already deleted" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Resource deletion complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Note: APIs are still enabled. To disable them, run:" -ForegroundColor Yellow
Write-Host "   gcloud services disable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com redis.googleapis.com storage-component.googleapis.com secretmanager.googleapis.com containerregistry.googleapis.com" -ForegroundColor Gray
Write-Host ""
Write-Host "💰 All resources have been deleted. You should see reduced billing." -ForegroundColor Cyan
Write-Host ""


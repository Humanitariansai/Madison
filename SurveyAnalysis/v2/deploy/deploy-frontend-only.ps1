# Simple script to rebuild and redeploy frontend only
# Usage: .\deploy\deploy-frontend-only.ps1 -ProjectId "your-project-id" -Region "us-central1"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

Write-Host "🚀 Deploying Frontend to Google Cloud" -ForegroundColor Green
Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get backend URL
Write-Host "Step 1: Getting backend URL..." -ForegroundColor Yellow
$backendUrl = gcloud run services describe survey-analysis-backend --region $Region --format='value(status.url)' 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($backendUrl) -or $backendUrl -match "ERROR") {
    Write-Host "❌ Error: Backend not found. Please deploy backend first." -ForegroundColor Red
    Write-Host "   Run: .\deploy\deploy-gcp.ps1 -ProjectId $ProjectId -Region $Region" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Backend URL: $backendUrl" -ForegroundColor Green
Write-Host ""

# Step 2: Navigate to frontend directory
Write-Host "Step 2: Preparing frontend directory..." -ForegroundColor Yellow
$scriptRoot = Split-Path -Parent $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = $PWD
}
$frontendDir = Join-Path $scriptRoot "frontend"

if (-not (Test-Path $frontendDir)) {
    Write-Host "❌ Error: Frontend directory not found at: $frontendDir" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir
Write-Host "✅ Working directory: $frontendDir" -ForegroundColor Green
Write-Host ""

# Step 3: Create .env.production file with backend URL
Write-Host "Step 3: Creating .env.production file..." -ForegroundColor Yellow

# Get Google Client ID (optional)
$googleClientId = ""
try {
    $googleClientId = gcloud secrets versions access latest --secret="google-client-id" 2>&1 | Out-String
    $googleClientId = $googleClientId.Trim()
    if ([string]::IsNullOrWhiteSpace($googleClientId)) {
        $googleClientId = ""
    }
} catch {
    Write-Host "⚠️  Google Client ID secret not found (optional)" -ForegroundColor Yellow
    $googleClientId = ""
}

# Create .env.production
$envContent = @"
VITE_API_BASE_URL=$backendUrl
VITE_GOOGLE_CLIENT_ID=$googleClientId
"@
$envContent | Out-File -FilePath .env.production -Encoding utf8
Write-Host "✅ Created .env.production" -ForegroundColor Green
Write-Host "   VITE_API_BASE_URL=$backendUrl" -ForegroundColor Cyan
Write-Host ""

# Step 4: Build Docker image and push to GCR
Write-Host "Step 4: Building Docker image..." -ForegroundColor Yellow
Write-Host "   This will build the image and push it to: gcr.io/$ProjectId/survey-analysis-frontend" -ForegroundColor Gray
Write-Host ""

$imageTag = "gcr.io/$ProjectId/survey-analysis-frontend"
gcloud builds submit --tag $imageTag .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "✅ Docker image built and pushed successfully!" -ForegroundColor Green
Write-Host ""

# Step 5: Deploy to Cloud Run
Write-Host "Step 5: Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy survey-analysis-frontend `
    --image $imageTag `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 256Mi `
    --cpu 1 `
    --max-instances 2 `
    --min-instances 0 `
    --port 80

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Deployment failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Get frontend URL
$frontendUrl = gcloud run services describe survey-analysis-frontend --region $Region --format='value(status.url)'

Pop-Location

Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host "🔧 Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your frontend is now live with the latest changes!" -ForegroundColor Green
Write-Host ""


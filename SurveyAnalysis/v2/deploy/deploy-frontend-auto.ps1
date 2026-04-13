# Auto-deploy frontend script - fetches all details automatically
# Usage: .\deploy\deploy-frontend-auto.ps1

Write-Host "[DEPLOY] Auto-Deploying Frontend to Google Cloud" -ForegroundColor Green
Write-Host ""

# Step 1: Get Project ID from gcloud config
Write-Host "Step 1: Fetching Project ID..." -ForegroundColor Yellow
$ProjectId = gcloud config get-value project 2>&1 | Out-String
$ProjectId = $ProjectId.Trim()

if ([string]::IsNullOrWhiteSpace($ProjectId) -or $ProjectId -match "ERROR") {
    Write-Host "[ERROR] Could not get Project ID from gcloud config" -ForegroundColor Red
    Write-Host "   Please run: gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Project ID: $ProjectId" -ForegroundColor Green
Write-Host ""

# Step 2: Get Region from existing services
Write-Host "Step 2: Detecting region..." -ForegroundColor Yellow
$Region = "us-central1"  # Default, but we'll verify from services

# Try to get region from existing services
$backendService = gcloud run services describe survey-analysis-backend --format="value(metadata.region)" 2>&1 | Out-String
$backendService = $backendService.Trim()
if ($backendService -and -not ($backendService -match "ERROR")) {
    $Region = $backendService
    Write-Host "[OK] Region detected: $Region" -ForegroundColor Green
} else {
    Write-Host "[WARN] Using default region: $Region" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Get backend URL
Write-Host "Step 3: Getting backend URL..." -ForegroundColor Yellow
$backendUrl = gcloud run services describe survey-analysis-backend --region $Region --format='value(status.url)' 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($backendUrl) -or $backendUrl -match "ERROR") {
    Write-Host "[ERROR] Backend not found. Please deploy backend first." -ForegroundColor Red
    Write-Host "   Run: .\deploy\deploy-gcp.ps1 -ProjectId $ProjectId -Region $Region" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Backend URL: $backendUrl" -ForegroundColor Green
Write-Host ""

# Step 4: Navigate to frontend directory
Write-Host "Step 4: Preparing frontend directory..." -ForegroundColor Yellow
$scriptRoot = Split-Path -Parent $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = $PWD
}
$frontendDir = Join-Path $scriptRoot "frontend"

if (-not (Test-Path $frontendDir)) {
    Write-Host "[ERROR] Frontend directory not found at: $frontendDir" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir
Write-Host "[OK] Working directory: $frontendDir" -ForegroundColor Green
Write-Host ""

# Step 5: Create .env.production file with backend URL
Write-Host "Step 5: Creating .env.production file..." -ForegroundColor Yellow

# Get Google Client ID (optional)
$googleClientId = ""
try {
    $googleClientId = gcloud secrets versions access latest --secret="google-client-id" 2>&1 | Out-String
    $googleClientId = $googleClientId.Trim()
    if ([string]::IsNullOrWhiteSpace($googleClientId)) {
        $googleClientId = ""
    }
} catch {
    Write-Host "[WARN] Google Client ID secret not found (optional)" -ForegroundColor Yellow
    $googleClientId = ""
}

# Create .env.production
$envContent = @"
VITE_API_BASE_URL=$backendUrl
VITE_GOOGLE_CLIENT_ID=$googleClientId
"@
$envContent | Out-File -FilePath .env.production -Encoding utf8
Write-Host "[OK] Created .env.production" -ForegroundColor Green
Write-Host "   VITE_API_BASE_URL=$backendUrl" -ForegroundColor Cyan
if ($googleClientId) {
    Write-Host "   VITE_GOOGLE_CLIENT_ID=$($googleClientId.Substring(0, [Math]::Min(30, $googleClientId.Length)))..." -ForegroundColor Cyan
}
Write-Host ""

# Step 6: Build Docker image and push to GCR
Write-Host "Step 6: Building Docker image..." -ForegroundColor Yellow
Write-Host "   Project: $ProjectId" -ForegroundColor Gray
Write-Host "   Region: $Region" -ForegroundColor Gray
Write-Host "   Image: gcr.io/$ProjectId/survey-analysis-frontend" -ForegroundColor Gray
Write-Host ""

$imageTag = "gcr.io/$ProjectId/survey-analysis-frontend"
gcloud builds submit --tag $imageTag .

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "[OK] Docker image built and pushed successfully!" -ForegroundColor Green
Write-Host ""

# Step 7: Deploy to Cloud Run
Write-Host "Step 7: Deploying to Cloud Run..." -ForegroundColor Yellow
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
    Write-Host "[ERROR] Deployment failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Get frontend URL
$frontendUrl = gcloud run services describe survey-analysis-frontend --region $Region --format='value(status.url)'

Pop-Location

Write-Host ""
Write-Host "[OK] Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Cyan
Write-Host "   Project ID: $ProjectId" -ForegroundColor White
Write-Host "   Region: $Region" -ForegroundColor White
Write-Host "   Backend URL: $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host 'Your frontend is now live with the latest changes!' -ForegroundColor Green
Write-Host ""


# Quick redeploy of frontend and backend code (no infrastructure changes)
# Usage: .\deploy\redeploy-code-only.ps1 -ProjectId "your-project-id" -Region "us-central1"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

Write-Host "[REDEPLOY] Redeploying Frontend and Backend Code" -ForegroundColor Green
Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host ""

# Set the project
Write-Host "[INFO] Setting project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

$scriptRoot = Split-Path -Parent $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = $PWD
}

# Step 1: Deploy Backend
Write-Host "`n[STEP 1/3] Building and deploying backend..." -ForegroundColor Yellow
$backendDir = Join-Path $scriptRoot "backend"
if (-not (Test-Path $backendDir)) {
    Write-Host "[ERROR] Backend directory not found at: $backendDir" -ForegroundColor Red
    exit 1
}

Push-Location $backendDir

Write-Host "Building backend Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-backend" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Backend Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Deploying backend to Cloud Run..." -ForegroundColor Gray

# Get Cloud SQL connection
$sqlConnection = gcloud sql instances describe survey-analysis-db --format="value(connectionName)" 2>&1 | Out-String
$sqlConnection = $sqlConnection.Trim()

# Get Qdrant internal IP (if exists)
Write-Host "Checking Qdrant VM..." -ForegroundColor Gray
$qdrantIpRaw = gcloud compute instances describe qdrant-vm --zone=us-central1-a --format='get(networkInterfaces[0].networkIP)' 2>&1
if ($LASTEXITCODE -eq 0) {
    $qdrantIp = $qdrantIpRaw.ToString().Trim()
    # Validate it's an actual IP address
    if ($qdrantIp -match '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
        Write-Host "[DEBUG] Qdrant IP retrieved: $qdrantIp" -ForegroundColor Gray
    } else {
        Write-Host "[WARN] Invalid Qdrant IP format: '$qdrantIp'" -ForegroundColor Yellow
        $qdrantIp = ""
    }
} else {
    Write-Host "[WARN] Qdrant VM not found or not accessible" -ForegroundColor Yellow
    $qdrantIp = ""
}

# Get Cloud SQL public IP for DATABASE_URL
Write-Host "Retrieving database credentials..." -ForegroundColor Gray
$sqlPublicIp = gcloud sql instances describe survey-analysis-db --format='get(ipAddresses[0].ipAddress)' 2>&1 | Out-String
$sqlPublicIp = $sqlPublicIp.Trim()

# Use public IP connection (required when VPC egress is private-ranges-only)
$databaseUrl = "postgresql://survey_user:0rjfd9qXW4hT3D2ABcwzmeEJ@${sqlPublicIp}:5432/survey_analysis"

$jwtSecret = ""
try {
    $jwtSecret = gcloud secrets versions access latest --secret="jwt-secret" 2>&1 | Out-String
    $jwtSecret = $jwtSecret.Trim()
} catch {
    Write-Host "[WARN] Could not retrieve JWT secret" -ForegroundColor Yellow
}

# Build environment variables
$gcsBucket = "$ProjectId-survey-analysis-files"
$redisUrl = "redis://10.12.234.139:6379/0"  # Cloud Memorystore internal IP

$envVars = "ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=30"
$envVars += ",REDIS_URL=$redisUrl"
$envVars += ",STORAGE_TYPE=gcs"
$envVars += ",GCS_BUCKET=$gcsBucket"
Write-Host "[INFO] Redis URL: $redisUrl" -ForegroundColor Green
Write-Host "[INFO] GCS Bucket: $gcsBucket" -ForegroundColor Green

if ($jwtSecret -and -not ($jwtSecret -match "ERROR")) {
    $envVars += ",SECRET_KEY=$jwtSecret"
}

if ($databaseUrl -and -not ($databaseUrl -match "ERROR")) {
    $envVars += ",DATABASE_URL=$databaseUrl"
    Write-Host "[INFO] Database URL configured" -ForegroundColor Green
} else {
    Write-Host "[ERROR] DATABASE_URL not found! Backend will fail." -ForegroundColor Red
}

if ($qdrantIp -and -not [string]::IsNullOrWhiteSpace($qdrantIp)) {
    $qdrantUrl = "http://${qdrantIp}:6333"
    $envVars += ",QDRANT_URL=$qdrantUrl"
    Write-Host "[INFO] Qdrant found at: $qdrantIp" -ForegroundColor Green
    Write-Host "[DEBUG] QDRANT_URL will be set to: $qdrantUrl" -ForegroundColor Gray
} else {
    Write-Host "[WARN] Qdrant VM not found. Vector DB features will be disabled." -ForegroundColor Yellow
}

# Deploy backend
# Note: Using --update-env-vars instead of --set-env-vars to preserve existing env vars (especially secrets)
Write-Host "[DEBUG] Environment variables string: $envVars" -ForegroundColor Gray

$deployCmd = "gcloud run deploy survey-analysis-backend " +
    "--image `"gcr.io/$ProjectId/survey-analysis-backend`" " +
    "--region $Region " +
    "--platform managed " +
    "--allow-unauthenticated " +
    "--memory 2Gi " +
    "--cpu 1 " +
    "--timeout 300 " +
    "--max-instances 3 " +
    "--min-instances 0 " +
    "--service-account `"survey-analysis-sa@$ProjectId.iam.gserviceaccount.com`" " +
    "--add-cloudsql-instances `"$sqlConnection`" " +
    "--vpc-connector cloudrun-connector " +
    "--vpc-egress private-ranges-only " +
    "--update-env-vars `"$envVars`""

# Check for OpenAI secret
$openaiSecretExists = gcloud secrets describe openai-api-key 2>&1 | Out-String
if ($LASTEXITCODE -eq 0 -and -not ($openaiSecretExists -match "ERROR")) {
    $deployCmd += " --update-secrets `"OPENAI_API_KEY=openai-api-key:latest`""
}

Invoke-Expression $deployCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Backend deployment failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

$backendUrl = gcloud run services describe survey-analysis-backend --region $Region --format='value(status.url)'
Write-Host "[OK] Backend deployed at: $backendUrl" -ForegroundColor Green

# Verify QDRANT_URL was set correctly
Write-Host "`n[VERIFY] Checking environment variables..." -ForegroundColor Gray
$deployedQdrantUrl = gcloud run services describe survey-analysis-backend --region $Region --format='value(spec.template.spec.containers[0].env.QDRANT_URL)' 2>&1
if ($deployedQdrantUrl -and $deployedQdrantUrl -match 'http://\d') {
    Write-Host "✅ QDRANT_URL verified: $deployedQdrantUrl" -ForegroundColor Green
} else {
    Write-Host "⚠️  QDRANT_URL may not be set correctly: $deployedQdrantUrl" -ForegroundColor Yellow
}

Pop-Location

# Step 2: Deploy Frontend
Write-Host "`n[STEP 2/3] Building and deploying frontend..." -ForegroundColor Yellow
$frontendDir = Join-Path $scriptRoot "frontend"
if (-not (Test-Path $frontendDir)) {
    Write-Host "[ERROR] Frontend directory not found at: $frontendDir" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir

# Get Google Client ID (optional)
$googleClientId = ""
try {
    $googleClientId = gcloud secrets versions access latest --secret="google-client-id" 2>&1 | Out-String
    $googleClientId = $googleClientId.Trim()
    if ([string]::IsNullOrWhiteSpace($googleClientId)) {
        $googleClientId = ""
    }
} catch {
    $googleClientId = ""
}

# Create .env.production
$envContent = @"
VITE_API_BASE_URL=$backendUrl
VITE_GOOGLE_CLIENT_ID=$googleClientId
"@
$envContent | Out-File -FilePath .env.production -Encoding utf8
Write-Host "[OK] Environment variables configured" -ForegroundColor Green

Write-Host "Building frontend Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-frontend" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Frontend Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Deploying frontend to Cloud Run..." -ForegroundColor Gray
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

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Frontend deployment failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

$frontendUrl = gcloud run services describe survey-analysis-frontend --region $Region --format='value(status.url)'

Pop-Location

# Step 3: Summary
Write-Host "`n[STEP 3/3] Deployment Summary" -ForegroundColor Yellow
Write-Host ""
Write-Host "[SUCCESS] Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Cyan
Write-Host "   Project ID: $ProjectId" -ForegroundColor White
Write-Host "   Region: $Region" -ForegroundColor White
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   Backend: $backendUrl" -ForegroundColor White
if ($qdrantIp -and -not ($qdrantIp -match "ERROR")) {
    Write-Host "   Qdrant: http://$qdrantIp:6333" -ForegroundColor White
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open frontend: $frontendUrl" -ForegroundColor White
Write-Host "2. Test API: $backendUrl/docs" -ForegroundColor White
Write-Host ""
Write-Host "Deployment took ~3-5 minutes" -ForegroundColor Gray
Write-Host ""

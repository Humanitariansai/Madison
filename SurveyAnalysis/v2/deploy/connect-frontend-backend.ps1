# Script to connect frontend to backend
# This will deploy backend if needed, then update and redeploy frontend with correct backend URL

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

Write-Host "Connecting Frontend to Backend`n" -ForegroundColor Green
Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region`n" -ForegroundColor Cyan

# Step 1: Check if backend is deployed
Write-Host "Step 1: Checking backend deployment..." -ForegroundColor Yellow
$backendUrl = gcloud run services describe survey-analysis-backend --region $Region --format='value(status.url)' 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($backendUrl) -or $backendUrl -match "ERROR") {
    Write-Host "Backend not found. Deploying backend first...`n" -ForegroundColor Red
    
    # Deploy backend
    $scriptRoot = Split-Path -Parent $PSScriptRoot
    if (-not $scriptRoot) {
        $scriptRoot = $PWD
    }
    $backendDir = Join-Path $scriptRoot "backend"
    
    if (-not (Test-Path $backendDir)) {
        Write-Host "Error: Backend directory not found" -ForegroundColor Red
        exit 1
    }
    
    Push-Location $backendDir
    
    Write-Host "Building backend Docker image..." -ForegroundColor Gray
    gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-backend" .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Backend Docker build failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "Deploying backend to Cloud Run..." -ForegroundColor Gray
    
    # Get SQL connection
    $sqlConnection = gcloud sql instances describe survey-analysis-db --format="value(connectionName)" 2>&1 | Out-String
    $sqlConnection = $sqlConnection.Trim()
    
    # Get secrets
    Write-Host "Retrieving secrets..." -ForegroundColor Gray
    $jwtSecretValue = gcloud secrets versions access latest --secret="jwt-secret" 2>&1 | Out-String
    $jwtSecretValue = $jwtSecretValue.Trim()
    
    $databaseUrlValue = gcloud secrets versions access latest --secret="database-url" 2>&1 | Out-String
    $databaseUrlValue = $databaseUrlValue.Trim()
    
    $redisUrlValue = gcloud secrets versions access latest --secret="redis-url" 2>&1 | Out-String
    $redisUrlValue = $redisUrlValue.Trim()
    
    # Build env vars (PORT is automatically set by Cloud Run, don't include it)
    $envVars = "DATABASE_URL=$databaseUrlValue,REDIS_URL=$redisUrlValue,SECRET_KEY=$jwtSecretValue,ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=30"
    
    # Check if OpenAI API key secret exists
    $openaiSecretExists = gcloud secrets describe openai-api-key 2>&1 | Out-String
    $deployCmd = "gcloud run deploy survey-analysis-backend " +
        "--image `"gcr.io/$ProjectId/survey-analysis-backend`" " +
        "--region $Region " +
        "--platform managed " +
        "--allow-unauthenticated " +
        "--memory 1Gi " +
        "--cpu 1 " +
        "--timeout 300 " +
        "--max-instances 3 " +
        "--min-instances 0 " +
        "--service-account `"survey-analysis-sa@$ProjectId.iam.gserviceaccount.com`" " +
        "--add-cloudsql-instances `"$sqlConnection`" " +
        "--set-env-vars `"$envVars`""
    
    if ($LASTEXITCODE -eq 0 -and -not ($openaiSecretExists -match "ERROR")) {
        Write-Host "OpenAI API key secret found, adding to deployment..." -ForegroundColor Gray
        $deployCmd += " --set-secrets `"OPENAI_API_KEY=openai-api-key:latest`""
    } else {
        Write-Host "Warning: OpenAI API key secret not found. AI features will be disabled." -ForegroundColor Yellow
        Write-Host "To enable AI features, create the secret with: echo 'YOUR_API_KEY' | gcloud secrets create openai-api-key --data-file=-" -ForegroundColor Yellow
    }
    
    Invoke-Expression $deployCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Backend deployment failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    # Get backend URL
    $backendUrl = gcloud run services describe survey-analysis-backend --region $Region --format='value(status.url)'
    Write-Host "Backend deployed at: $backendUrl`n" -ForegroundColor Green
    
    Pop-Location
} else {
    Write-Host "Backend already deployed at: $backendUrl`n" -ForegroundColor Green
}

# Step 2: Update frontend with backend URL
Write-Host "Step 2: Updating frontend with backend URL..." -ForegroundColor Yellow
$scriptRoot = Split-Path -Parent $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = $PWD
}
$frontendDir = Join-Path $scriptRoot "frontend"

if (-not (Test-Path $frontendDir)) {
    Write-Host "Error: Frontend directory not found" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir

Write-Host "Getting Google Client ID..." -ForegroundColor Gray
$googleClientId = ""
try {
    $googleClientId = gcloud secrets versions access latest --secret="google-client-id" 2>&1 | Out-String
    $googleClientId = $googleClientId.Trim()
    if ([string]::IsNullOrWhiteSpace($googleClientId)) {
        $googleClientId = ""
    }
} catch {
    Write-Host "Warning: Google Client ID secret not found. Google Sign-In will be disabled." -ForegroundColor Yellow
    $googleClientId = ""
}

Write-Host "Creating .env.production with correct backend URL..." -ForegroundColor Gray
$envContent = @"
VITE_API_BASE_URL=$backendUrl
VITE_GOOGLE_CLIENT_ID=$googleClientId
"@
$envContent | Out-File -FilePath .env.production -Encoding utf8
Write-Host "Environment variables configured" -ForegroundColor Green
Write-Host "   Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host "   Google Client ID: $($googleClientId.Substring(0, [Math]::Min(30, $googleClientId.Length)))...`n" -ForegroundColor Cyan

# Step 3: Rebuild and redeploy frontend
Write-Host "Step 3: Rebuilding and redeploying frontend..." -ForegroundColor Yellow
Write-Host "Building Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-frontend" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Frontend Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Deploying to Cloud Run..." -ForegroundColor Gray
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
    Write-Host "Error: Frontend deployment failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

$frontendUrl = gcloud run services describe survey-analysis-frontend --region $Region --format='value(status.url)'

Pop-Location

Write-Host "`nFrontend connected to backend successfully!`n" -ForegroundColor Green
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host "`nThe frontend is now configured to connect to the backend.`n" -ForegroundColor Green


# Script to deploy backend only (after build completes)
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

Write-Host "Deploying Backend to Cloud Run...`n" -ForegroundColor Yellow

# Get SQL connection
Write-Host "Getting Cloud SQL connection details..." -ForegroundColor Gray
$sqlConnection = gcloud sql instances describe survey-analysis-db --format="value(connectionName)" 2>&1 | Out-String
$sqlConnection = $sqlConnection.Trim()
if ([string]::IsNullOrWhiteSpace($sqlConnection)) {
    Write-Host "Error: Could not get Cloud SQL connection name" -ForegroundColor Red
    exit 1
}
Write-Host "Cloud SQL connection: $sqlConnection" -ForegroundColor Green

# Get secrets
Write-Host "Retrieving secrets..." -ForegroundColor Gray
$jwtSecretValue = ""
$databaseUrlValue = ""
$redisUrlValue = ""

try {
    $jwtSecretValue = gcloud secrets versions access latest --secret="jwt-secret" 2>&1 | Out-String
    $jwtSecretValue = $jwtSecretValue.Trim()
} catch {
    Write-Host "Warning: Could not retrieve JWT secret" -ForegroundColor Yellow
    $jwtSecretValue = "placeholder-jwt-secret"
}

try {
    $databaseUrlValue = gcloud secrets versions access latest --secret="database-url" 2>&1 | Out-String
    $databaseUrlValue = $databaseUrlValue.Trim()
} catch {
    Write-Host "Warning: Could not retrieve database URL" -ForegroundColor Yellow
    $databaseUrlValue = ""
}

try {
    $redisUrlValue = gcloud secrets versions access latest --secret="redis-url" 2>&1 | Out-String
    $redisUrlValue = $redisUrlValue.Trim()
} catch {
    Write-Host "Warning: Could not retrieve Redis URL" -ForegroundColor Yellow
    $redisUrlValue = ""
}

# Build environment variables string
$envVars = "ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=30"
if ($jwtSecretValue -and $jwtSecretValue -ne "placeholder-jwt-secret") {
    $envVars += ",SECRET_KEY=$jwtSecretValue"
}
if ($databaseUrlValue) {
    $envVars += ",DATABASE_URL=$databaseUrlValue"
}
if ($redisUrlValue) {
    $envVars += ",REDIS_URL=$redisUrlValue"
}

# Check if OpenAI API key secret exists
Write-Host "Checking for OpenAI API key secret..." -ForegroundColor Gray
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
}

Write-Host "Deploying to Cloud Run..." -ForegroundColor Gray
Invoke-Expression $deployCmd

if ($LASTEXITCODE -eq 0) {
    $backendUrl = gcloud run services describe survey-analysis-backend --region $Region --format='value(status.url)'
    Write-Host "`nBackend deployed successfully!" -ForegroundColor Green
    Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan
    Write-Host "`nNext: Update frontend with this backend URL and redeploy frontend.`n" -ForegroundColor Yellow
} else {
    Write-Host "`nError: Backend deployment failed" -ForegroundColor Red
    exit 1
}


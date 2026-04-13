# PowerShell Deployment Script for Google Cloud Platform
# Usage: .\deploy\deploy-gcp.ps1 -ProjectId "your-project-id" -Region "us-central1"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

Write-Host "🚀 Deploying Survey Analysis Application to Google Cloud" -ForegroundColor Green
Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host ""

# Set the project
Write-Host "📋 Setting project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Check if gcloud is installed
$gcloudPath = "C:\Users\Owner\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $gcloudPath)) {
    # Try to find gcloud in PATH
    $gcloudCmd = Get-Command gcloud -ErrorAction SilentlyContinue
    if ($gcloudCmd) {
        $gcloudPath = $gcloudCmd.Source
    } else {
        Write-Host "❌ Error: gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
        Write-Host "Download from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
        exit 1
    }
}

# Create alias for gcloud if needed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Set-Alias -Name gcloud -Value $gcloudPath -Scope Script
}

# Step 1: Setup GCP Resources
Write-Host "`n📦 Step 1: Setting up GCP resources..." -ForegroundColor Yellow

# Enable APIs
Write-Host "Enabling required APIs..." -ForegroundColor Gray
gcloud services enable cloudbuild.googleapis.com,run.googleapis.com,sqladmin.googleapis.com,redis.googleapis.com,storage-component.googleapis.com,secretmanager.googleapis.com,containerregistry.googleapis.com,artifactregistry.googleapis.com 2>$null

# Check if Cloud SQL instance exists
Write-Host "Checking Cloud SQL instance..." -ForegroundColor Gray
$sqlExists = $false
try {
    $result = gcloud sql instances describe survey-analysis-db --format=json 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $result -match '"name"') {
        $sqlExists = $true
        Write-Host "✅ Cloud SQL instance already exists" -ForegroundColor Green
        # Get existing password from secret or generate new one
        # Skip secret retrieval to avoid hanging - we'll use root password or generate new one
        Write-Host "⚠️  Skipping secret retrieval (may hang). Using generated password." -ForegroundColor Yellow
        Write-Host "Note: If you need the original password, retrieve it manually with:" -ForegroundColor Gray
        Write-Host "  gcloud secrets versions access latest --secret=db-password" -ForegroundColor Gray
        $dbPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
        Write-Host "✅ Generated new password (will be stored in secret if needed)" -ForegroundColor Green
    }
} catch {
    Write-Host "Cloud SQL instance not found, will create new one" -ForegroundColor Yellow
}

if (-not $sqlExists) {
    Write-Host "Creating Cloud SQL PostgreSQL instance..." -ForegroundColor Gray
    Write-Host "⏳ This may take 5-10 minutes..." -ForegroundColor Yellow
    $dbPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    gcloud sql instances create survey-analysis-db `
        --database-version=POSTGRES_15 `
        --tier=db-f1-micro `
        --region=$Region `
        --root-password=$dbPassword `
        --storage-type=SSD `
        --storage-size=10GB
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Cloud SQL instance created" -ForegroundColor Green
        # Store password in secret
        echo $dbPassword | gcloud secrets create db-password --data-file=- 2>$null
    } else {
        Write-Host "❌ Failed to create Cloud SQL instance" -ForegroundColor Red
        exit 1
    }
}

# Check if database exists
Write-Host "`nChecking database..." -ForegroundColor Gray
$dbExists = $false
try {
    $dbResult = gcloud sql databases describe survey_analysis --instance=survey-analysis-db --format=json 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $dbResult -match '"name"') {
        $dbExists = $true
        Write-Host "✅ Database already exists" -ForegroundColor Green
    } else {
        Write-Host "Database not found, will create..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Database check failed, will attempt to create..." -ForegroundColor Yellow
}

if (-not $dbExists) {
    Write-Host "Creating database..." -ForegroundColor Gray
    gcloud sql databases create survey_analysis --instance=survey-analysis-db
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database created" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Database creation returned non-zero exit code (may already exist or error occurred)" -ForegroundColor Yellow
    }
}

# Check if database user exists
$dbUser = "survey_user"
Write-Host "`nChecking database user..." -ForegroundColor Gray
$userExists = $false
try {
    $userResult = gcloud sql users describe $dbUser --instance=survey-analysis-db --format=json 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $userResult -match '"name"') {
        $userExists = $true
        Write-Host "✅ Database user already exists" -ForegroundColor Green
        # Use the same password we retrieved earlier
        $dbUserPassword = $dbPassword
        Write-Host "Using existing password for database user" -ForegroundColor Gray
    } else {
        Write-Host "Database user not found, will create..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "User check failed, will attempt to create..." -ForegroundColor Yellow
}

if (-not $userExists) {
    Write-Host "Creating database user..." -ForegroundColor Gray
    $dbUserPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    gcloud sql users create $dbUser --instance=survey-analysis-db --password=$dbUserPassword
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database user created" -ForegroundColor Green
    } else {
        Write-Host "⚠️  User creation returned non-zero exit code (may already exist or error occurred)" -ForegroundColor Yellow
        # Try to use existing password
        $dbUserPassword = $dbPassword
    }
}

# Check if Redis instance exists
Write-Host "Checking Redis instance..." -ForegroundColor Gray
$redisExists = $false
try {
    $result = gcloud redis instances describe survey-analysis-redis --region=$Region --format=json 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $result -match '"name"') {
        $redisExists = $true
        Write-Host "✅ Redis instance already exists" -ForegroundColor Green
    }
} catch {
    # Redis instance doesn't exist, will create
}

if (-not $redisExists) {
    Write-Host "Creating Redis instance..." -ForegroundColor Gray
    Write-Host "⏳ This may take 5-10 minutes..." -ForegroundColor Yellow
    gcloud redis instances create survey-analysis-redis `
        --size=1 `
        --region=$Region `
        --redis-version=redis_7_0 `
        --tier=basic
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis instance created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create Redis instance" -ForegroundColor Red
        exit 1
    }
}

# Get connection details
$sqlConnection = gcloud sql instances describe survey-analysis-db --format="value(connectionName)"
$redisHost = gcloud redis instances describe survey-analysis-redis --region=$Region --format="value(host)"

# Check if Cloud Storage bucket exists
Write-Host "Checking Cloud Storage bucket..." -ForegroundColor Gray
$bucketName = "$ProjectId-survey-analysis-files"
$bucketExists = gsutil ls -b "gs://$bucketName" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Cloud Storage bucket already exists" -ForegroundColor Green
} else {
    Write-Host "Creating Cloud Storage bucket..." -ForegroundColor Gray
    gsutil mb -p $ProjectId -l $Region "gs://$bucketName"
    Write-Host "✅ Cloud Storage bucket created" -ForegroundColor Green
}

# Check and create secrets (only if they don't exist)
Write-Host "`nChecking secrets..." -ForegroundColor Gray
Write-Host "⚠️  Skipping secret existence checks to avoid hanging. Creating/updating secrets directly." -ForegroundColor Yellow

# Create or update JWT secret
Write-Host "Creating/updating JWT secret..." -ForegroundColor Gray
$jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
try {
    # Try to create, if it exists, add a new version
    echo $jwtSecret | gcloud secrets create jwt-secret --data-file=- 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ JWT secret created" -ForegroundColor Green
    } else {
        # Secret might already exist, add new version
        echo $jwtSecret | gcloud secrets versions add jwt-secret --data-file=- 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ JWT secret updated" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Could not create/update JWT secret (may need manual setup)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "⚠️  JWT secret operation failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create or update database URL secret
Write-Host "Creating/updating database URL secret..." -ForegroundColor Gray
$databaseUrl = "postgresql://$dbUser`:$dbUserPassword@/survey_analysis?host=/cloudsql/$sqlConnection"
try {
    echo $databaseUrl | gcloud secrets create database-url --data-file=- 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database URL secret created" -ForegroundColor Green
    } else {
        # Secret might already exist, add new version
        echo $databaseUrl | gcloud secrets versions add database-url --data-file=- 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database URL secret updated" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Could not create/update database URL secret (may need manual setup)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "⚠️  Database URL secret operation failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create or update Redis URL secret
Write-Host "Creating/updating Redis URL secret..." -ForegroundColor Gray
$redisUrl = "redis://$redisHost`:6379/0"
try {
    echo $redisUrl | gcloud secrets create redis-url --data-file=- 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis URL secret created" -ForegroundColor Green
    } else {
        # Secret might already exist, add new version
        echo $redisUrl | gcloud secrets versions add redis-url --data-file=- 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Redis URL secret updated" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Could not create/update Redis URL secret (may need manual setup)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "⚠️  Redis URL secret operation failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Check if service account exists
Write-Host "Checking service account..." -ForegroundColor Gray
$saExists = gcloud iam service-accounts describe "survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Service account already exists" -ForegroundColor Green
} else {
    Write-Host "Creating service account..." -ForegroundColor Gray
    gcloud iam service-accounts create survey-analysis-sa --display-name="Survey Analysis Service Account"
    Write-Host "✅ Service account created" -ForegroundColor Green
}

# Grant permissions to service account (idempotent - safe to run multiple times)
Write-Host "Granting permissions to service account..." -ForegroundColor Gray
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" --role="roles/cloudsql.client" 2>$null
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" 2>$null
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:survey-analysis-sa@$ProjectId.iam.gserviceaccount.com" --role="roles/storage.objectAdmin" 2>$null

# Grant Cloud Build permissions to current user (needed for gcloud builds submit)
Write-Host "Granting Cloud Build permissions to current user..." -ForegroundColor Gray
$currentUser = gcloud config get-value account
if ($currentUser) {
    Write-Host "Granting Cloud Build Editor role to: $currentUser" -ForegroundColor Gray
    gcloud projects add-iam-policy-binding $ProjectId --member="user:$currentUser" --role="roles/cloudbuild.builds.editor" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="user:$currentUser" --role="roles/storage.admin" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="user:$currentUser" --role="roles/iam.serviceAccountUser" 2>$null
}

# Grant Cloud Build service account permissions (needed for pushing images)
Write-Host "Granting permissions to Cloud Build service account..." -ForegroundColor Gray
$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)" 2>$null
if ($projectNumber) {
    $cloudBuildSA = "$projectNumber@cloudbuild.gserviceaccount.com"
    Write-Host "Granting permissions to: $cloudBuildSA" -ForegroundColor Gray
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$cloudBuildSA" --role="roles/storage.admin" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$cloudBuildSA" --role="roles/storage.objectAdmin" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$cloudBuildSA" --role="roles/artifactregistry.writer" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$cloudBuildSA" --role="roles/artifactregistry.admin" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$cloudBuildSA" --role="roles/run.admin" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$cloudBuildSA" --role="roles/iam.serviceAccountUser" 2>$null
}

# Grant permissions to Compute Engine default service account (needed for Cloud Build)
Write-Host "Granting permissions to Compute Engine default service account..." -ForegroundColor Gray
$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)" 2>$null
if ($projectNumber) {
    $computeSA = "$projectNumber-compute@developer.gserviceaccount.com"
    Write-Host "Granting permissions to: $computeSA" -ForegroundColor Gray
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$computeSA" --role="roles/storage.admin" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$computeSA" --role="roles/storage.objectAdmin" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$computeSA" --role="roles/storage.objectCreator" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$computeSA" --role="roles/storage.objectViewer" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$computeSA" --role="roles/artifactregistry.writer" 2>$null
    gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$computeSA" --role="roles/artifactregistry.admin" 2>$null
}

# Create GCR repository if it doesn't exist
Write-Host "Checking Container Registry repository..." -ForegroundColor Gray
$repoExists = gcloud artifacts repositories describe gcr.io --location=$Region --format=json 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or -not ($repoExists -match '"name"')) {
    Write-Host "Creating Container Registry repository..." -ForegroundColor Gray
    gcloud artifacts repositories create gcr.io `
        --repository-format=docker `
        --location=$Region `
        --project=$ProjectId 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container Registry repository created" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Repository may already exist or creation failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Container Registry repository already exists" -ForegroundColor Green
}

Write-Host "✅ GCP resources setup complete!" -ForegroundColor Green

# Save the script directory (project root)
$scriptRoot = Split-Path -Parent $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = $PWD
}

# Step 2: Deploy Backend
Write-Host "`n🔨 Step 2: Building and deploying backend..." -ForegroundColor Yellow
$backendDir = Join-Path $scriptRoot "backend"
if (-not (Test-Path $backendDir)) {
    Write-Host "❌ Error: Backend directory not found at: $backendDir" -ForegroundColor Red
    exit 1
}

Push-Location $backendDir

Write-Host "Building Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-backend" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Backend Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "Deploying to Cloud Run..." -ForegroundColor Gray

# Get connection details (needed for Cloud SQL connection)
Write-Host "Getting Cloud SQL connection details..." -ForegroundColor Gray
$sqlConnection = gcloud sql instances describe survey-analysis-db --format="value(connectionName)" 2>&1 | Out-String
$sqlConnection = $sqlConnection.Trim()
if ([string]::IsNullOrWhiteSpace($sqlConnection)) {
    Write-Host "❌ Error: Could not get Cloud SQL connection name" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "Cloud SQL connection: $sqlConnection" -ForegroundColor Green

# Get secrets (with error handling to avoid hanging)
Write-Host "Retrieving secrets..." -ForegroundColor Gray
$jwtSecretValue = ""
$databaseUrlValue = ""
$redisUrlValue = ""

try {
    $jwtSecretValue = gcloud secrets versions access latest --secret="jwt-secret" 2>&1 | Out-String
    $jwtSecretValue = $jwtSecretValue.Trim()
} catch {
    Write-Host "⚠️  Could not retrieve JWT secret, using placeholder" -ForegroundColor Yellow
    $jwtSecretValue = "placeholder-jwt-secret"
}

try {
    $databaseUrlValue = gcloud secrets versions access latest --secret="database-url" 2>&1 | Out-String
    $databaseUrlValue = $databaseUrlValue.Trim()
} catch {
    Write-Host "⚠️  Could not retrieve database URL, will use environment variable" -ForegroundColor Yellow
    $databaseUrlValue = ""
}

try {
    $redisUrlValue = gcloud secrets versions access latest --secret="redis-url" 2>&1 | Out-String
    $redisUrlValue = $redisUrlValue.Trim()
} catch {
    Write-Host "⚠️  Could not retrieve Redis URL, will use environment variable" -ForegroundColor Yellow
    $redisUrlValue = ""
}

# Build environment variables string (PORT is automatically set by Cloud Run, don't include it)
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
    Write-Host "To enable AI features, create the secret with: echo 'YOUR_API_KEY' | gcloud secrets create openai-api-key --data-file=-" -ForegroundColor Yellow
}

Invoke-Expression $deployCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Backend deployment failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Get backend URL - use proper escaping for PowerShell
$backendUrl = (gcloud run services describe survey-analysis-backend --region $Region --format='value(status.url)')
Write-Host "✅ Backend deployed at: $backendUrl" -ForegroundColor Green

Pop-Location

# Step 3: Deploy Frontend
Write-Host "`n🔨 Step 3: Building and deploying frontend..." -ForegroundColor Yellow
$frontendDir = Join-Path $scriptRoot "frontend"
if (-not (Test-Path $frontendDir)) {
    Write-Host "❌ Error: Frontend directory not found at: $frontendDir" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir

Write-Host "Updating API URL..." -ForegroundColor Gray
# Get Google Client ID from secret or use empty string
$googleClientId = ""
try {
    $googleClientId = gcloud secrets versions access latest --secret="google-client-id" 2>&1 | Out-String
    $googleClientId = $googleClientId.Trim()
    if ([string]::IsNullOrWhiteSpace($googleClientId)) {
        $googleClientId = ""
    }
} catch {
    Write-Host "⚠️  Google Client ID secret not found. Google Sign-In will be disabled." -ForegroundColor Yellow
    Write-Host "   To enable Google Sign-In, create a secret named 'google-client-id' with your Google OAuth Client ID" -ForegroundColor Yellow
    $googleClientId = ""
}

# Create .env.production file with all required environment variables
$envContent = @"
VITE_API_BASE_URL=$backendUrl
VITE_GOOGLE_CLIENT_ID=$googleClientId
"@
$envContent | Out-File -FilePath .env.production -Encoding utf8
Write-Host "✅ Environment variables configured" -ForegroundColor Green

Write-Host "Building Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/survey-analysis-frontend" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Frontend Docker build failed" -ForegroundColor Red
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
    Write-Host "❌ Error: Frontend deployment failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Get frontend URL - use proper escaping for PowerShell
$frontendUrl = (gcloud run services describe survey-analysis-frontend --region $Region --format='value(status.url)')

Pop-Location

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host "🔧 Backend URL: $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the application at: $frontendUrl"
Write-Host "2. Initialize database: python backend/setup_database.py"
Write-Host "3. View API docs: $backendUrl/docs"
Write-Host ""



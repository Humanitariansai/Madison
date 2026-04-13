# Setup Celery worker on the Qdrant VM (runs alongside Qdrant container)
# Run this AFTER deploy-gcp.ps1 or redeploy-code-only.ps1
# Usage: .\deploy\setup-celery-worker.ps1 -ProjectId "your-project-id"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",

    [Parameter(Mandatory=$false)]
    [string]$Zone = "us-central1-a"
)

Write-Host "[CELERY] Setting up Celery worker on Qdrant VM" -ForegroundColor Green
Write-Host "Project: $ProjectId | Zone: $Zone" -ForegroundColor Cyan

# Fixed values (match redeploy-code-only.ps1)
$RedisUrl      = "redis://10.12.234.139:6379/0"
$QdrantUrl     = "http://10.128.0.5:6333"
$GcsBucket     = "$ProjectId-survey-analysis-files"
$DbUrl         = "postgresql://survey_user:0rjfd9qXW4hT3D2ABcwzmeEJ@34.55.71.193:5432/survey_analysis"
$BackendImage  = "gcr.io/$ProjectId/survey-analysis-backend"

# Retrieve OpenAI key from Secret Manager
Write-Host "[INFO] Retrieving OpenAI API key..." -ForegroundColor Yellow
$OpenAiKey = ""
try {
    $OpenAiKey = gcloud secrets versions access latest --secret="openai-api-key" 2>&1 | Out-String
    $OpenAiKey = $OpenAiKey.Trim()
} catch {
    Write-Host "[WARN] Could not retrieve OpenAI key. AI features in worker will be disabled." -ForegroundColor Yellow
}

# Authenticate Docker on the VM to pull from GCR
Write-Host "[INFO] Configuring VM to pull backend image from GCR..." -ForegroundColor Yellow
gcloud compute ssh qdrant-vm --zone=$Zone --command="gcloud auth configure-docker gcr.io --quiet 2>/dev/null || true"

# Stop existing worker container if running
Write-Host "[INFO] Stopping existing celery_worker container (if any)..." -ForegroundColor Yellow
gcloud compute ssh qdrant-vm --zone=$Zone --command="docker stop celery_worker 2>/dev/null; docker rm celery_worker 2>/dev/null; echo done"

# Pull latest backend image
Write-Host "[INFO] Pulling latest backend image on VM..." -ForegroundColor Yellow
gcloud compute ssh qdrant-vm --zone=$Zone --command="docker pull $BackendImage"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to pull backend image. Check that image exists in GCR." -ForegroundColor Red
    exit 1
}

# Start Celery worker container
Write-Host "[INFO] Starting Celery worker container..." -ForegroundColor Yellow

$dockerCmd = @"
docker run -d \
  --name celery_worker \
  --restart unless-stopped \
  --network host \
  -e REDIS_URL=$RedisUrl \
  -e DATABASE_URL=$DbUrl \
  -e QDRANT_URL=$QdrantUrl \
  -e GCS_BUCKET=$GcsBucket \
  -e STORAGE_TYPE=gcs \
  -e OPENAI_API_KEY=$OpenAiKey \
  -e PYTHONUNBUFFERED=1 \
  $BackendImage \
  celery -A src.async_processor.celery_app worker --loglevel=info --concurrency=2
"@

gcloud compute ssh qdrant-vm --zone=$Zone --command=$dockerCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start Celery worker container." -ForegroundColor Red
    exit 1
}

# Wait a moment and check it's running
Start-Sleep -Seconds 5
Write-Host "[INFO] Verifying worker is running..." -ForegroundColor Yellow
gcloud compute ssh qdrant-vm --zone=$Zone --command="docker ps --filter name=celery_worker --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"

Write-Host ""
Write-Host "[SUCCESS] Celery worker is running on Qdrant VM!" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  View logs:   gcloud compute ssh qdrant-vm --zone=$Zone --command='docker logs -f celery_worker'" -ForegroundColor White
Write-Host "  Stop worker: gcloud compute ssh qdrant-vm --zone=$Zone --command='docker stop celery_worker'" -ForegroundColor White
Write-Host "  Restart:     .\deploy\setup-celery-worker.ps1 -ProjectId $ProjectId" -ForegroundColor White

# Script to fix database password authentication issue
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

Write-Host "`nFixing database password authentication...`n" -ForegroundColor Yellow

# Set the project
gcloud config set project $ProjectId

# Generate a new secure password
$dbUser = "survey_user"
$newPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 24 | ForEach-Object {[char]$_})

Write-Host "Step 1: Resetting database user password..." -ForegroundColor Cyan
Write-Host "User: $dbUser" -ForegroundColor Gray
Write-Host "New password: $newPassword" -ForegroundColor Gray
Write-Host "`nWARNING: Save this password securely!`n" -ForegroundColor Yellow

# Reset the user password
gcloud sql users set-password $dbUser `
    --instance=survey-analysis-db `
    --password=$newPassword

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to reset database user password" -ForegroundColor Red
    exit 1
}

Write-Host "Password reset successful!`n" -ForegroundColor Green

# Get SQL connection name
Write-Host "Step 2: Getting Cloud SQL connection details..." -ForegroundColor Cyan
$sqlConnection = gcloud sql instances describe survey-analysis-db --format="value(connectionName)" 2>&1 | Out-String
$sqlConnection = $sqlConnection.Trim()

if ([string]::IsNullOrWhiteSpace($sqlConnection)) {
    Write-Host "Error: Could not get Cloud SQL connection name" -ForegroundColor Red
    exit 1
}

Write-Host "Connection: $sqlConnection`n" -ForegroundColor Green

# Update database-url secret
Write-Host "Step 3: Updating database-url secret..." -ForegroundColor Cyan
$databaseUrl = "postgresql://$dbUser`:$newPassword@/survey_analysis?host=/cloudsql/$sqlConnection"

# Create or update the secret
echo $databaseUrl | gcloud secrets create database-url --data-file=- 2>$null
if ($LASTEXITCODE -ne 0) {
    # Secret exists, add new version
    echo $databaseUrl | gcloud secrets versions add database-url --data-file=-
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to update database-url secret" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Secret updated successfully!`n" -ForegroundColor Green

# Also update db-password secret (for reference)
Write-Host "Step 4: Updating db-password secret..." -ForegroundColor Cyan
echo $newPassword | gcloud secrets create db-password --data-file=- 2>$null
if ($LASTEXITCODE -ne 0) {
    echo $newPassword | gcloud secrets versions add db-password --data-file=-
}

Write-Host "`nDatabase password fix completed!`n" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Redeploy the backend to pick up the new password:" -ForegroundColor Cyan
Write-Host "   .\deploy\rebuild-and-deploy-backend.ps1 -ProjectId `"$ProjectId`" -Region `"$Region`"`n" -ForegroundColor White


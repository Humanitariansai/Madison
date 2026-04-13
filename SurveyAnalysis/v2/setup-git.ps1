# Script to set up git and connect to Madison repository
# Usage: .\setup-git.ps1

Write-Host "`nSetting up Git connection to Madison repository...`n" -ForegroundColor Yellow

# Check if git is installed
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitInstalled) {
    Write-Host "Error: Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

# Initialize git if not already initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Cyan
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to initialize git repository" -ForegroundColor Red
        exit 1
    }
    Write-Host "Git repository initialized`n" -ForegroundColor Green
} else {
    Write-Host "Git repository already initialized`n" -ForegroundColor Green
}

# Check current remote
Write-Host "Checking current remote configuration..." -ForegroundColor Cyan
$currentRemote = git remote -v 2>&1 | Out-String

if ($currentRemote -match "Madison") {
    Write-Host "Remote 'origin' already points to Madison repository" -ForegroundColor Yellow
    Write-Host "Current remote: $currentRemote" -ForegroundColor Gray
} else {
    # Add remote
    Write-Host "Adding Madison repository as remote 'origin'..." -ForegroundColor Cyan
    git remote add origin https://github.com/Humanitariansai/Madison.git 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        # Remote might already exist, try to set URL
        Write-Host "Remote 'origin' exists, updating URL..." -ForegroundColor Yellow
        git remote set-url origin https://github.com/Humanitariansai/Madison.git
    }
    
    Write-Host "Remote 'origin' configured`n" -ForegroundColor Green
}

# Verify remote
Write-Host "Verifying remote configuration..." -ForegroundColor Cyan
git remote -v
Write-Host ""

# Check if there are uncommitted changes
Write-Host "Checking git status..." -ForegroundColor Cyan
$status = git status --porcelain 2>&1 | Out-String

if ($status.Trim()) {
    Write-Host "You have uncommitted changes. Here's what needs to be committed:" -ForegroundColor Yellow
    git status
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Review the changes above" -ForegroundColor White
    Write-Host "2. Add files: git add ." -ForegroundColor White
    Write-Host "3. Commit: git commit -m 'Your commit message'" -ForegroundColor White
    Write-Host "4. Fetch from remote: git fetch origin" -ForegroundColor White
    Write-Host "5. Push to SurveyAnalysis folder: git push origin main:main" -ForegroundColor White
} else {
    Write-Host "No uncommitted changes found." -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Fetch from remote: git fetch origin" -ForegroundColor White
    Write-Host "2. Check if you want to merge with existing SurveyAnalysis folder" -ForegroundColor White
    Write-Host "3. Push your code: git push origin main:main" -ForegroundColor White
}

Write-Host "`nNote: The Madison repository already has a SurveyAnalysis folder." -ForegroundColor Yellow
Write-Host "You may want to:" -ForegroundColor Yellow
Write-Host "- Create a new branch for your changes" -ForegroundColor White
Write-Host "- Or coordinate with the repository maintainers about merging" -ForegroundColor White
Write-Host "`n"


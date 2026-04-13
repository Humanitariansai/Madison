# Script to push code to SurveyAnalysisV2 folder in Madison repository's main branch
# Usage: .\push-to-madison-v2.ps1

Write-Host "`nSetting up Git and pushing to SurveyAnalysisV2 folder in main branch...`n" -ForegroundColor Yellow

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

# Add remote
Write-Host "Configuring remote repository..." -ForegroundColor Cyan
$remoteExists = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Remote 'origin' already exists, updating URL..." -ForegroundColor Yellow
    git remote set-url origin https://github.com/Humanitariansai/Madison.git
} else {
    Write-Host "Adding remote 'origin'..." -ForegroundColor Cyan
    git remote add origin https://github.com/Humanitariansai/Madison.git
}

Write-Host "Remote configured: https://github.com/Humanitariansai/Madison.git`n" -ForegroundColor Green

# Fetch from remote to get main branch
Write-Host "Fetching from remote repository..." -ForegroundColor Cyan
git fetch origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Could not fetch from remote. You may need to authenticate." -ForegroundColor Yellow
    Write-Host "Make sure you have access to the repository.`n" -ForegroundColor Yellow
}

# Check if we're on main branch or need to switch
$currentBranch = git branch --show-current 2>&1
if (-not $currentBranch -or $currentBranch -eq "") {
    # Check if main branch exists locally
    $mainExists = git branch --list main 2>&1
    if ($mainExists) {
        Write-Host "Switching to main branch..." -ForegroundColor Cyan
        git checkout main
    } else {
        # Try to checkout main from remote
        Write-Host "Checking out main branch from remote..." -ForegroundColor Cyan
        git checkout -b main origin/main 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            # If remote main doesn't exist or can't be fetched, create local main
            Write-Host "Creating new main branch..." -ForegroundColor Cyan
            git checkout -b main
        }
    }
    $currentBranch = "main"
} elseif ($currentBranch -ne "main") {
    Write-Host "Current branch is '$currentBranch'. Switching to main..." -ForegroundColor Yellow
    git checkout main 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        git checkout -b main
    }
    $currentBranch = "main"
}

Write-Host "Current branch: $currentBranch`n" -ForegroundColor Green

# Check if SurveyAnalysisV2 folder already exists in the repo
Write-Host "Checking if SurveyAnalysisV2 folder exists in repository..." -ForegroundColor Cyan
$v2Exists = Test-Path "SurveyAnalysisV2"
if ($v2Exists) {
    Write-Host "Warning: SurveyAnalysisV2 folder already exists locally." -ForegroundColor Yellow
    Write-Host "This script will organize your current code into that folder.`n" -ForegroundColor Yellow
}

# Create temporary directory to organize files
Write-Host "Organizing files into SurveyAnalysisV2 folder structure..." -ForegroundColor Cyan

# Get the current directory (where the script is running from)
$currentDir = Get-Location
$parentDir = Split-Path -Parent $currentDir
$tempDir = Join-Path $env:TEMP "survey-analysis-v2-temp"

# Create temp directory
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

Write-Host "Copying files to temporary directory..." -ForegroundColor Gray

# Copy all files except .git to temp directory
Get-ChildItem -Path $currentDir -Force | Where-Object { 
    $_.Name -ne ".git" -and $_.Name -ne "SurveyAnalysisV2"
} | ForEach-Object {
    $destPath = Join-Path $tempDir $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -Path $_.FullName -Destination $destPath -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $destPath -Force
    }
}

# Create SurveyAnalysisV2 folder in current directory
if (-not (Test-Path "SurveyAnalysisV2")) {
    New-Item -ItemType Directory -Path "SurveyAnalysisV2" -Force | Out-Null
}

# Move files from temp to SurveyAnalysisV2
Write-Host "Moving files to SurveyAnalysisV2 folder..." -ForegroundColor Gray
Get-ChildItem -Path $tempDir | ForEach-Object {
    $destPath = Join-Path "SurveyAnalysisV2" $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -Path $_.FullName -Destination $destPath -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $destPath -Force
    }
}

# Clean up temp directory
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "Files organized into SurveyAnalysisV2 folder`n" -ForegroundColor Green

# Add all files
Write-Host "Adding all files to git..." -ForegroundColor Cyan
git add .

# Check if there are changes to commit
$status = git status --porcelain 2>&1 | Out-String
if ($status.Trim()) {
    Write-Host "Creating commit..." -ForegroundColor Cyan
    git commit -m "Add SurveyAnalysisV2: Complete survey analysis application with AI features, GCP deployment, and comprehensive analysis capabilities"
    Write-Host "Commit created`n" -ForegroundColor Green
} else {
    Write-Host "No changes to commit.`n" -ForegroundColor Yellow
}

Write-Host "Ready to push to main branch!`n" -ForegroundColor Green
Write-Host "Your code will be pushed to: SurveyAnalysisV2/ folder in the main branch`n" -ForegroundColor Cyan

# Ask if user wants to push now
$pushNow = Read-Host "Do you want to push to main branch now? (y/n)"
if ($pushNow -eq "y" -or $pushNow -eq "Y") {
    Write-Host "`nPushing to main branch..." -ForegroundColor Cyan
    Write-Host "Note: You may be prompted for GitHub credentials`n" -ForegroundColor Yellow
    
    # Push to main branch
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nSuccessfully pushed to main branch!`n" -ForegroundColor Green
        Write-Host "View your code at:" -ForegroundColor Cyan
        Write-Host "https://github.com/Humanitariansai/Madison/tree/main/SurveyAnalysisV2`n" -ForegroundColor White
    } else {
        Write-Host "`nPush failed. You may need to:" -ForegroundColor Yellow
        Write-Host "1. Authenticate with GitHub (use GitHub CLI or personal access token)" -ForegroundColor White
        Write-Host "2. Check if you have write access to the repository" -ForegroundColor White
        Write-Host "3. Pull and merge any remote changes first:" -ForegroundColor White
        Write-Host "   git pull origin main --allow-unrelated-histories" -ForegroundColor Gray
        Write-Host "   Then try pushing again: git push origin main`n" -ForegroundColor Gray
    }
} else {
    Write-Host "`nSkipping push. Your code is organized in SurveyAnalysisV2 folder." -ForegroundColor Yellow
    Write-Host "When ready, run: git push -u origin main`n" -ForegroundColor White
}

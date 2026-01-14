# Script to push code to SurveyAnalysisV2 folder in Madison repository
# Usage: .\push-to-madison-v2.ps1

Write-Host "`nSetting up Git and pushing to SurveyAnalysisV2 in Madison repository...`n" -ForegroundColor Yellow

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

# Fetch from remote to see existing branches
Write-Host "Fetching from remote repository..." -ForegroundColor Cyan
git fetch origin
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Could not fetch from remote. You may need to authenticate." -ForegroundColor Yellow
    Write-Host "Make sure you have access to the repository.`n" -ForegroundColor Yellow
}

# Check current branch
$currentBranch = git branch --show-current 2>&1
if (-not $currentBranch -or $currentBranch -eq "") {
    Write-Host "No branch exists yet. Creating initial commit..." -ForegroundColor Cyan
    
    # Add all files
    Write-Host "Adding all files..." -ForegroundColor Gray
    git add .
    
    # Create initial commit
    Write-Host "Creating initial commit..." -ForegroundColor Gray
    git commit -m "Initial commit: Survey Analysis V2 Application"
    
    # Create and checkout main branch
    git branch -M main
    $currentBranch = "main"
}

Write-Host "Current branch: $currentBranch`n" -ForegroundColor Green

# Show status
Write-Host "Current git status:" -ForegroundColor Cyan
git status --short
Write-Host ""

# Check if there are uncommitted changes
$status = git status --porcelain 2>&1 | Out-String
if ($status.Trim()) {
    Write-Host "You have uncommitted changes. Adding and committing..." -ForegroundColor Yellow
    git add .
    git commit -m "Update: Survey Analysis V2 - Latest changes"
    Write-Host "Changes committed`n" -ForegroundColor Green
}

Write-Host "Ready to push to Madison repository!`n" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Push to a new branch (recommended):" -ForegroundColor White
Write-Host "   git push -u origin $currentBranch:SurveyAnalysisV2" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Or push to main branch:" -ForegroundColor White
Write-Host "   git push -u origin $currentBranch" -ForegroundColor Gray
Write-Host ""
Write-Host "3. After pushing, you can:" -ForegroundColor White
Write-Host "   - Create a Pull Request on GitHub" -ForegroundColor Gray
Write-Host "   - Or merge directly if you have write access" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: To push to SurveyAnalysisV2 folder, you may need to:" -ForegroundColor Yellow
Write-Host "- Create the folder structure in the repository first, OR" -ForegroundColor White
Write-Host "- Push to a branch and organize via GitHub web interface`n" -ForegroundColor White

# Ask if user wants to push now
$pushNow = Read-Host "Do you want to push now? (y/n)"
if ($pushNow -eq "y" -or $pushNow -eq "Y") {
    Write-Host "`nPushing to remote..." -ForegroundColor Cyan
    Write-Host "Note: You may be prompted for GitHub credentials`n" -ForegroundColor Yellow
    
    # Try to push to a branch named after SurveyAnalysisV2
    Write-Host "Attempting to push to branch: SurveyAnalysisV2" -ForegroundColor Gray
    git push -u origin $currentBranch:SurveyAnalysisV2
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nSuccessfully pushed to SurveyAnalysisV2 branch!`n" -ForegroundColor Green
        Write-Host "View your code at:" -ForegroundColor Cyan
        Write-Host "https://github.com/Humanitariansai/Madison/tree/SurveyAnalysisV2`n" -ForegroundColor White
    } else {
        Write-Host "`nPush failed. You may need to:" -ForegroundColor Yellow
        Write-Host "1. Authenticate with GitHub (use GitHub CLI or personal access token)" -ForegroundColor White
        Write-Host "2. Check if you have write access to the repository" -ForegroundColor White
        Write-Host "3. Try pushing manually with: git push -u origin $currentBranch`n" -ForegroundColor White
    }
} else {
    Write-Host "`nSkipping push. Run the push command manually when ready.`n" -ForegroundColor Yellow
}


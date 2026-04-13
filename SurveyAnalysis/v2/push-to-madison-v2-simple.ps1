param(
    [switch]$SkipPush
)

if (-not (Test-Path ".git")) {
    git init
}

$remoteCheck = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    git remote set-url origin https://github.com/Humanitariansai/Madison.git
} else {
    git remote add origin https://github.com/Humanitariansai/Madison.git
}

git fetch origin main --no-tags 2>&1 | Out-Null

if (Test-Path "SurveyAnalysisV2") {
    Remove-Item -Path "SurveyAnalysisV2" -Recurse -Force
}

New-Item -ItemType Directory -Path "SurveyAnalysisV2" -Force | Out-Null

Get-ChildItem -Path . -Force | Where-Object { 
    $_.Name -ne ".git" -and $_.Name -ne "SurveyAnalysisV2" 
} | ForEach-Object {
    $dest = Join-Path "SurveyAnalysisV2" $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $dest -Force
    }
}

git add .
git commit -m "Add SurveyAnalysisV2: Complete survey analysis application" 2>&1 | Out-Null

$currentBranch = git branch --show-current 2>&1
if (-not $currentBranch -or $currentBranch -ne "main") {
    git branch -M main 2>&1 | Out-Null
}

$remoteMainExists = git show-ref --verify --quiet refs/remotes/origin/main 2>&1
if ($LASTEXITCODE -eq 0) {
    git merge origin/main --allow-unrelated-histories -m "Merge remote main branch with SurveyAnalysisV2" 2>&1 | Out-Null
}

if (-not $SkipPush) {
    git push -u origin main
}

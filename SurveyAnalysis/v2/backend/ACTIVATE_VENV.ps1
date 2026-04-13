# PowerShell script to activate virtual environment
# Usage: .\ACTIVATE_VENV.ps1

if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    .\venv\Scripts\activate.ps1
    Write-Host "Virtual environment activated! (venv)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Python version:" -ForegroundColor Cyan
    python --version
    Write-Host ""
    Write-Host "To deactivate, type: deactivate" -ForegroundColor Yellow
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: setup_venv.bat" -ForegroundColor Yellow
}


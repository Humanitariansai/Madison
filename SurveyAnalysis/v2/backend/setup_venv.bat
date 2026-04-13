@echo off
REM Setup script for Windows to create and configure virtual environment

echo ========================================
echo Setting up Python Virtual Environment
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment created

echo.
echo [2/5] Virtual environment created
echo.
echo NOTE: To activate, run:
echo   PowerShell: .\venv\Scripts\activate.ps1
echo   Command Prompt: venv\Scripts\activate.bat
echo.

echo.
echo [3/5] Upgrading pip...
python -m pip install --upgrade pip
echo ✓ Pip upgraded

echo.
echo [4/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

echo.
echo [5/5] Setup complete!
echo.
echo ========================================
echo Next steps:
echo ========================================
echo 1. Activate venv: venv\Scripts\activate
echo 2. Create .env file with your configuration
echo 3. Initialize database: python src\db_init.py
echo 4. Run server: python run.py
echo.
echo ========================================
pause


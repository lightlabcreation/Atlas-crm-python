# PowerShell script to run Django development server on Windows

Write-Host "Starting Atlas CRM Django Server..." -ForegroundColor Green

# Check if Python is available
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Test-Path "C:\Python313\python.exe") {
    $pythonCmd = "C:\Python313\python.exe"
} else {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Or enable Python from Microsoft Store" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    .\venv\Scripts\Activate.ps1
} elseif (Test-Path "venv\bin\activate") {
    Write-Host "Virtual environment found (Linux-style), please activate manually" -ForegroundColor Yellow
    Write-Host "Run: venv\bin\activate (if using WSL/Git Bash)" -ForegroundColor Yellow
}

# Set DEBUG environment variable
$env:DEBUG = "True"

# Run migrations first
Write-Host "`nRunning database migrations..." -ForegroundColor Cyan
& $pythonCmd manage.py migrate --noinput

# Collect static files if needed
Write-Host "Collecting static files..." -ForegroundColor Cyan
& $pythonCmd manage.py collectstatic --noinput 2>$null

# Start the development server
Write-Host "`nStarting Django development server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow
& $pythonCmd manage.py runserver


# Local Development Server Start Script
# This will run Django on http://localhost:8000

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Atlas CRM - Local Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for Python
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    Write-Host "[OK] Python found" -ForegroundColor Green
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
    Write-Host "[OK] Python found (via py launcher)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[OK] Activating virtual environment..." -ForegroundColor Green
    try {
        .\venv\Scripts\Activate.ps1
    } catch {
        Write-Host "[WARNING] Execution policy issue. Running fix..." -ForegroundColor Yellow
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        .\venv\Scripts\Activate.ps1
    }
} else {
    Write-Host "[WARNING] Virtual environment not found" -ForegroundColor Yellow
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    & $pythonCmd -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt
}

Write-Host ""

# Set environment variables
$env:DEBUG = "True"
$env:DJANGO_SETTINGS_MODULE = "crm_fulfillment.settings"

Write-Host "[INFO] Running database migrations..." -ForegroundColor Cyan
& $pythonCmd manage.py migrate --noinput

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Django Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Local URL:    http://localhost:8000" -ForegroundColor Green
# Write-Host "  Production:   https://atlas.kiaantechnology.com" -ForegroundColor Yellow
Write-Host "  Production:   https://web-production-5ba14555.up.railway.app" -ForegroundColor Yellow

Write-Host ""
Write-Host "  Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

& $pythonCmd manage.py runserver 8000


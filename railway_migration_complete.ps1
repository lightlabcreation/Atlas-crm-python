# Complete Railway Database Migration Script
# यह script सभी steps automatically run करेगा

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Railway Database Migration - Complete Process" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Railway CLI
Write-Host "Step 1: Checking Railway CLI..." -ForegroundColor Yellow
$railwayCheck = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railwayCheck) {
    Write-Host "Railway CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g @railway/cli
}

# Step 2: Check login
Write-Host ""
Write-Host "Step 2: Checking login status..." -ForegroundColor Yellow
$loginCheck = railway whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Please login..." -ForegroundColor Yellow
    railway login
}

# Step 3: Run migrations
Write-Host ""
Write-Host "Step 3: Running migrations..." -ForegroundColor Yellow
railway run python manage.py migrate

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error running migrations!" -ForegroundColor Red
    pause
    exit 1
}

# Step 4: Import data
Write-Host ""
Write-Host "Step 4: Importing data..." -ForegroundColor Yellow

if (-not (Test-Path "db_export.json")) {
    Write-Host ""
    Write-Host "db_export.json file not found!" -ForegroundColor Red
    Write-Host "Please run export_local_database.ps1 first." -ForegroundColor Yellow
    pause
    exit 1
}

railway run python manage.py loaddata db_export.json

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error importing data!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Create superuser" -ForegroundColor Yellow
Write-Host "  railway run python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


# Railway Commands Script for Windows PowerShell
# यह script Railway पर migrate और createsuperuser commands चलाएगा

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Railway Database Setup Commands" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Railway CLI is installed
Write-Host "Checking Railway CLI..." -ForegroundColor Yellow
$railwayCheck = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railwayCheck) {
    Write-Host "❌ Railway CLI not found. Installing..." -ForegroundColor Red
    npm install -g @railway/cli
    Write-Host "✅ Railway CLI installed" -ForegroundColor Green
}

# Check if logged in
Write-Host ""
Write-Host "Checking Railway login status..." -ForegroundColor Yellow
$loginCheck = railway whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Not logged in to Railway" -ForegroundColor Yellow
    Write-Host "Please login first:" -ForegroundColor Yellow
    Write-Host "  railway login" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This will open a browser window for authentication." -ForegroundColor Yellow
    Write-Host ""
    $login = Read-Host "Press Enter to open Railway login (or Ctrl+C to cancel)"
    railway login
}

# Check if linked to project
Write-Host ""
Write-Host "Checking Railway project link..." -ForegroundColor Yellow
$linkCheck = railway status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Not linked to Railway project" -ForegroundColor Yellow
    Write-Host "Please link to your project:" -ForegroundColor Yellow
    Write-Host "  railway link" -ForegroundColor Cyan
    Write-Host ""
    $link = Read-Host "Press Enter to link Railway project (or Ctrl+C to cancel)"
    railway link
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Database Migrations..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
railway run python manage.py migrate

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Migrations completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Creating Superuser..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You will be prompted to enter:" -ForegroundColor Yellow
    Write-Host "  - Username" -ForegroundColor Yellow
    Write-Host "  - Email" -ForegroundColor Yellow
    Write-Host "  - Password" -ForegroundColor Yellow
    Write-Host ""
    railway run python manage.py createsuperuser
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Superuser created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "Setup Complete! 🎉" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Error creating superuser" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "❌ Error running migrations" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  1. DATABASE_URL is set in Railway variables" -ForegroundColor Yellow
    Write-Host "  2. PostgreSQL database is added to Railway project" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


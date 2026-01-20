@echo off
REM Railway Commands Script for Windows CMD
REM यह script Railway पर migrate और createsuperuser commands चलाएगा

echo ========================================
echo Railway Database Setup Commands
echo ========================================
echo.

REM Check if Railway CLI is installed
echo Checking Railway CLI...
railway --version >nul 2>&1
if errorlevel 1 (
    echo Railway CLI not found. Installing...
    call npm install -g @railway/cli
    echo Railway CLI installed
)

REM Check if logged in
echo.
echo Checking Railway login status...
railway whoami >nul 2>&1
if errorlevel 1 (
    echo Not logged in to Railway
    echo Please login first:
    echo   railway login
    echo.
    echo This will open a browser window for authentication.
    echo.
    pause
    railway login
)

REM Check if linked to project
echo.
echo Checking Railway project link...
railway status >nul 2>&1
if errorlevel 1 (
    echo Not linked to Railway project
    echo Please link to your project:
    echo   railway link
    echo.
    pause
    railway link
)

echo.
echo ========================================
echo Running Database Migrations...
echo ========================================
echo.
railway run python manage.py migrate

if errorlevel 1 (
    echo.
    echo Error running migrations
    echo Please check:
    echo   1. DATABASE_URL is set in Railway variables
    echo   2. PostgreSQL database is added to Railway project
    pause
    exit /b 1
)

echo.
echo Migrations completed successfully!
echo.
echo ========================================
echo Creating Superuser...
echo ========================================
echo.
echo You will be prompted to enter:
echo   - Username
echo   - Email
echo   - Password
echo.
railway run python manage.py createsuperuser

if errorlevel 1 (
    echo.
    echo Error creating superuser
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
pause


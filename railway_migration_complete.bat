@echo off
REM Complete Railway Database Migration Script
REM यह script सभी steps automatically run करेगा

echo ========================================
echo Railway Database Migration - Complete Process
echo ========================================
echo.

echo Step 1: Checking Railway CLI...
railway --version >nul 2>&1
if errorlevel 1 (
    echo Railway CLI not found. Installing...
    call npm install -g @railway/cli
)

echo.
echo Step 2: Checking login status...
railway whoami >nul 2>&1
if errorlevel 1 (
    echo Not logged in. Please login...
    railway login
)

echo.
echo Step 3: Running migrations...
railway run python manage.py migrate
if errorlevel 1 (
    echo Error running migrations!
    pause
    exit /b 1
)

echo.
echo Step 4: Importing data...
if not exist db_export.json (
    echo db_export.json file not found!
    echo Please run export_local_database.bat first.
    pause
    exit /b 1
)

railway run python manage.py loaddata db_export.json
if errorlevel 1 (
    echo Error importing data!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Migration Complete!
echo ========================================
echo.
echo Next: Create superuser
echo   railway run python manage.py createsuperuser
echo.
pause


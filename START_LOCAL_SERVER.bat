@echo off
REM Local Development Server Start Script
REM This will run Django on http://localhost:8000

echo ========================================
echo   Atlas CRM - Local Development Server
echo ========================================
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :found_python
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto :found_python
)

echo [ERROR] Python not found!
echo.
echo Please install Python from: https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation
echo.
pause
exit /b 1

:found_python
echo [OK] Python found
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [OK] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo [INFO] Setting up environment...
set DEBUG=True
set DJANGO_SETTINGS_MODULE=crm_fulfillment.settings

echo.
echo [INFO] Running database migrations...
%PYTHON_CMD% manage.py migrate --noinput

echo.
echo ========================================
echo   Starting Django Development Server
echo ========================================
echo.
echo   Server URL: http://localhost:8000
echo   Production: https://atlas.kiaantechnology.com
echo.
echo   Press Ctrl+C to stop the server
echo ========================================
echo.

%PYTHON_CMD% manage.py runserver 8000

pause


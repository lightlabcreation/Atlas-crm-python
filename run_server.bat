@echo off
REM Batch script to run Django development server on Windows

echo Starting Atlas CRM Django Server...

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

if exist "C:\Python313\python.exe" (
    set PYTHON_CMD=C:\Python313\python.exe
    goto :found_python
)

echo ERROR: Python not found!
echo Please install Python 3.8+ from https://www.python.org/downloads/
pause
exit /b 1

:found_python
REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Set DEBUG
set DEBUG=True

REM Run migrations
echo Running database migrations...
%PYTHON_CMD% manage.py migrate --noinput

REM Start server
echo.
echo Starting Django development server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
%PYTHON_CMD% manage.py runserver

pause


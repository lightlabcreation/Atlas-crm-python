# Local Development Setup Guide

## Python Installation Required

To run the Django server locally, you need Python 3.8 or higher installed.

### Install Python:

1. **Download Python**: https://www.python.org/downloads/
2. **During installation**: Check "Add Python to PATH"
3. **Verify installation**: Open a new terminal and run:
   ```powershell
   python --version
   ```

## Running the Server

### Option 1: Using the Run Script (Easiest)

**PowerShell:**
```powershell
.\run_server.ps1
```

**Command Prompt:**
```cmd
run_server.bat
```

### Option 2: Manual Commands

1. **Activate Virtual Environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   Or if using Command Prompt:
   ```cmd
   venv\Scripts\activate.bat
   ```

2. **Install Dependencies (if needed):**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run Migrations:**
   ```powershell
   python manage.py migrate
   ```

4. **Collect Static Files:**
   ```powershell
   python manage.py collectstatic --noinput
   ```

5. **Start Development Server:**
   ```powershell
   python manage.py runserver
   ```

## Access the Application

Once the server starts, open your browser and go to:
- **Frontend & Backend**: http://localhost:8000

The Django server serves both the backend API and frontend templates.

## Troubleshooting

### If Python is not found:
- Install Python from https://www.python.org/downloads/
- Make sure "Add Python to PATH" is checked during installation
- Restart your terminal after installation

### If virtual environment is not working:
- Recreate it: `python -m venv venv`
- Then activate it and install dependencies: `pip install -r requirements.txt`

### Port already in use:
- If port 8000 is busy, use a different port: `python manage.py runserver 8080`
- Or stop the process using port 8000


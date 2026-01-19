# Python Install aur Server Chalane ka Guide (Hindi)

## Problem: Python Install Nahin Hai

Aapko `ERR_CONNECTION_REFUSED` aa raha hai kyunki **Django server abhi run nahi ho raha** hai. Server chalane ke liye Python chahiye.

---

## Solution: Step-by-Step

### Step 1: Python Install Karen

**Option A: Official Python Website Se (Recommended)**
1. https://www.python.org/downloads/ par jayein
2. **"Download Python 3.12.x"** button par click karein
3. Downloaded file ko run karein
4. **Important**: Installation ke time **"Add Python to PATH"** checkbox ko ✅ check karein (bahut zaruri hai!)
5. "Install Now" par click karein

**Option B: Microsoft Store Se (Easier)**
1. Windows Store open karein
2. "Python 3.12" search karein
3. Install karein

---

### Step 2: Terminal Restart Karen

Python install hone ke baad:
- **Current terminal window ko band karein**
- **Nayi terminal/PowerShell window open karein**
- Current directory me jayein:
  ```powershell
  cd "d:\atlas project-17-jan-26\atlas-crm"
  ```

---

### Step 3: Python Verify Karen

Nayi terminal me ye command run karein:
```powershell
python --version
```

Agar "Python 3.x.x" dikhe to Python sahi se install hai! ✅

---

### Step 4: Virtual Environment Setup Karen

```powershell
# Virtual environment create karein (agar nahi hai to)
python -m venv venv

# Virtual environment activate karein
.\venv\Scripts\Activate.ps1
```

Agar PowerShell execution policy ki error aaye, to pehle ye run karein:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Step 5: Dependencies Install Karen

```powershell
pip install -r requirements.txt
```

Ye thoda time lega, wait karein.

---

### Step 6: Database Migrations Run Karen

```powershell
python manage.py migrate
```

---

### Step 7: Server Start Karen! 🚀

```powershell
python manage.py runserver
```

Agar sab kuch sahi ho to aapko dikhega:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 8: Browser Mein Kholo

Ab Chrome mein ye URL open karein:
```
http://localhost:8000/
```

Ya:
```
http://127.0.0.1:8000/
```

---

## Agar Phir Bhi Problem Ho To:

### Check Karen:
1. ✅ Python install hai? (`python --version`)
2. ✅ Virtual environment activate hai? (command prompt pe `(venv)` dikhna chahiye)
3. ✅ Dependencies install ho gaye? (`pip list` se check karein)
4. ✅ Server running hai? (Terminal me "Starting development server" dikhna chahiye)

### Common Errors:

**Error: "python is not recognized"**
→ Python install nahi hai ya PATH me add nahi hai
→ Solution: Python reinstall karein aur "Add to PATH" check karein

**Error: "Port 8000 already in use"**
→ Koi aur program port 8000 use kar raha hai
→ Solution: Different port use karein:
  ```powershell
  python manage.py runserver 8080
  ```

**Error: "No module named 'django'"**
→ Dependencies install nahi hain
→ Solution: `pip install -r requirements.txt` run karein

---

## Quick One-Line Commands (Jab Python Install Ho Jaye):

PowerShell me ye sab ek saath:
```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; python manage.py migrate; python manage.py runserver
```

---

**Agar aapko Python install me madad chahiye ya koi aur error aa raha hai, to bataiye!**


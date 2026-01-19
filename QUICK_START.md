# 🚀 Quick Start - Server Chalane Ke Liye

## ⚠️ Problem: Python Install Nahin Hai

Aapko `ERR_CONNECTION_REFUSED` aa raha hai kyunki **Django server abhi run nahi ho raha**.

---

## ✅ Solution: 3 Simple Steps

### Step 1: Python Install Karen (2 minutes)

**Option 1: Microsoft Store (Sabse Aasan)**
1. Windows Start Menu me "Microsoft Store" search karein
2. "Python 3.12" search karein
3. "Install" button par click karein
4. Install hone ka wait karein

**Option 2: Official Website**
1. Browser me jayein: https://www.python.org/downloads/
2. "Download Python 3.12.x" button par click karein
3. Downloaded file run karein
4. **Important**: "Add Python to PATH" ✅ check karein
5. "Install Now" click karein

---

### Step 2: Terminal Restart Karen

- **Current PowerShell/Terminal window ko band karein**
- **Nayi PowerShell window open karein**
- Project folder me jayein:
  ```powershell
  cd "d:\atlas project-17-jan-26\atlas-crm"
  ```

---

### Step 3: Ye Commands Run Karen (Copy-Paste)

```powershell
# Python check karein
python --version

# Virtual environment activate karein
.\venv\Scripts\Activate.ps1

# Agar activation me error aaye, to pehle ye run karein:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Dependencies install karein (pehli baar)
pip install -r requirements.txt

# Database setup karein
python manage.py migrate

# Server start karein! 🎉
python manage.py runserver
```

---

## 🎯 Expected Output

Jab server start ho jayega, aapko terminal me dikhega:

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**Ab Chrome me jayein: http://localhost:8000/**

---

## ❌ Agar Error Aaye To:

### "python is not recognized"
→ Python install nahi hai ya PATH me nahi hai
→ Solution: Python reinstall karein aur "Add to PATH" check karein

### "Execution Policy" error
→ PowerShell me ye run karein:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### "Port 8000 already in use"
→ Different port use karein:
  ```powershell
  python manage.py runserver 8080
  ```

---

## 📞 Help Chahiye?

Agar Python install karne me ya kisi aur step me problem ho, to bataiye!


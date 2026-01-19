# 🚀 Localhost Par Server Chalane Ke Liye - Abhi

## ⚠️ Important: Python Install Karna Zaruri Hai

Abhi aapke system me **Python install nahi hai** ya PATH me nahi hai. Isliye server start nahi ho sakta.

---

## ✅ Quick Fix (2 Minutes):

### Step 1: Python Install Karen

**Sabse Aasan Tarika - Microsoft Store:**
1. Windows Start Menu me **"Microsoft Store"** search karein
2. **"Python 3.12"** search karein  
3. **"Install"** button par click karein
4. Install hone ka wait karein (1-2 minutes)

**Ya Official Website Se:**
- https://www.python.org/downloads/
- Download karein aur install karein
- **"Add Python to PATH"** ✅ check karein (bahut zaruri!)

---

### Step 2: VS Code Terminal Restart Karen

1. VS Code me **Terminal tab ko close** karein
2. **Nayi terminal open** karein (Ctrl + `)
3. Ye command run karein:
   ```powershell
   python --version
   ```
   
   Agar "Python 3.x.x" dikhe to ✅ ready hai!

---

### Step 3: Server Start Karen (Copy-Paste Ye Commands)

VS Code terminal me ye sab commands ek-ek karke run karein:

```powershell
# 1. Virtual environment activate karein
.\venv\Scripts\Activate.ps1

# Agar error aaye (Execution Policy), to pehle ye run karein:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

```powershell
# 2. Dependencies check karein (agar pehle se install nahi hain)
pip install -r requirements.txt
```

```powershell
# 3. Database setup karein
python manage.py migrate
```

```powershell
# 4. Server start karein! 🎉
python manage.py runserver 8000
```

---

## 🎯 Expected Output:

Jab server start ho jayega, aapko terminal me dikhega:

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**Ab browser me jayein: http://localhost:8000/**

---

## 📝 One-Line Command (Jab Python Install Ho Jaye):

Agar aap sab kuch ek saath run karna chahte hain:

```powershell
.\venv\Scripts\Activate.ps1; pip install -r requirements.txt; python manage.py migrate; python manage.py runserver 8000
```

---

## ❓ Help Chahiye?

Agar Python install me ya kisi aur step me problem ho, to bataiye!

**Note:** Python install hone ke baad hi server start ho sakta hai. Abhi Python nahi hai isliye `ERR_CONNECTION_REFUSED` aa raha hai.


# Railway Commands चलाने के लिए Instructions

## ✅ Git Push Complete!
आपके सभी changes git में push हो गए हैं। Railway automatically deploy करेगा।

---

## 🚀 Railway Commands चलाने के 2 तरीके:

### Method 1: Script Use करें (आसान) ⭐

**PowerShell में:**
```powershell
.\run_railway_commands.ps1
```

**या CMD में:**
```cmd
run_railway_commands.bat
```

यह script automatically:
- Railway CLI check करेगा
- Login करवाएगा (अगर नहीं है)
- Project link करेगा (अगर नहीं है)
- Migrations run करेगा
- Superuser create करवाएगा

---

### Method 2: Manual Commands

**Step 1: Railway Login करें**
```bash
railway login
```
(Browser खुलेगा, वहां login करें)

**Step 2: Project Link करें (अगर नहीं है)**
```bash
railway link
```
(अपने project को select करें)

**Step 3: Migrations Run करें**
```bash
railway run python manage.py migrate
```

**Step 4: Superuser Create करें**
```bash
railway run python manage.py createsuperuser
```
(Username, Email, Password enter करें)

---

## ⚠️ Important Notes:

1. **पहले Railway Dashboard में PostgreSQL Database Add करें:**
   - Railway Dashboard → "+ New" → "Database" → "Add PostgreSQL"
   - यह automatically `DATABASE_URL` set कर देगा

2. **Git Push होने के बाद:**
   - Railway automatically deploy करेगा
   - 2-3 minutes wait करें
   - फिर commands run करें

3. **अगर Error आए:**
   - Check करें कि `DATABASE_URL` variable Railway में set है
   - Check करें कि PostgreSQL service "Online" है

---

## 📝 Quick Checklist:

- [ ] Git push complete ✅ (हो गया)
- [ ] Railway Dashboard में PostgreSQL database add करें
- [ ] Railway auto-deploy complete होने का wait करें
- [ ] `run_railway_commands.ps1` या `run_railway_commands.bat` चलाएं
- [ ] या manual commands run करें

---

**सब कुछ ready है! बस Railway में database add करें और commands run करें।** 🎉


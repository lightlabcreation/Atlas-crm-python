# Complete Database Migration Guide - Railway पर Database Setup

## ✅ Current Status:
- ✅ Railway PostgreSQL already created
- ✅ DATABASE_URL mil gaya: `postgresql://postgres:APILoMaKLaigOsLSRonwfEsLvqXetmUM@postgres.railway.internal:5432/railway`

---

## 🟢 STEP 1 — LOCAL MACHINE par DATABASE EXPORT karo

### Option A: Django Built-in Command (Recommended)

**Terminal में (local project folder me):**

```bash
python manage.py dumpdata \
  --exclude contenttypes \
  --exclude auth.permission \
  --exclude sessions \
  --natural-foreign \
  --natural-primary \
  --indent 2 > db_export.json
```

**या Windows PowerShell में:**

```powershell
python manage.py dumpdata --exclude contenttypes --exclude auth.permission --exclude sessions --natural-foreign --natural-primary --indent 2 > db_export.json
```

### Option B: Export Script Use करें

```bash
python export_database.py
```

**✅ Output:** `db_export.json` file banegi

**⚠️ Important:** Is file ko GitHub me push mat karna (sensitive data hota hai) - `.gitignore` me add karo

---

## 🟢 STEP 2 — Railway Web Service me DATABASE_URL Confirm

**Railway Dashboard में:**

1. **"web"** service पर click करें
2. **"Variables"** tab पर जाएं
3. Check करें कि `DATABASE_URL` variable है:
   - Value: `${{Postgres.DATABASE_URL}}` (recommended)
   - या: `postgresql://postgres:APILoMaKLaigOsLSRonwfEsLvqXetmUM@postgres.railway.internal:5432/railway`

**अगर नहीं है, तो add करें:**
- **"+ New Variable"** click करें
- Name: `DATABASE_URL`
- Value: `${{Postgres.DATABASE_URL}}`
- **"Add"** click करें

---

## 🟢 STEP 3 — Railway par MIGRATIONS chalao (MOST IMPORTANT)

**Terminal में:**

```bash
# Login (अगर नहीं है)
railway login

# Project link करें
railway link

# Migrations run करें
railway run python manage.py migrate
```

**Expected Output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, ...
Running migrations:
  Applying migrations...
  ...
```

**✅ Tables create honi chahiye**

**⚠️ Import se pehle migrate zaroori hai!**

---

## 🟢 STEP 4 — Export file Railway container me le jao

### Option A: Git Push (Temporary - Recommended)

**⚠️ Important:** Import ke baad is file ko delete kar dena

```bash
# .gitignore me check करें (अगर db_export.json ignore नहीं है)
echo db_export.json >> .gitignore

# Temporary commit (import ke baad delete kar denge)
git add db_export.json
git commit -m "temp: add db export for Railway import"
git push
```

### Option B: Railway CLI se Upload

```bash
railway run bash
# Then inside container, manually upload file
```

---

## 🟢 STEP 5 — Railway par DATA IMPORT karo

**Terminal में:**

```bash
railway run python manage.py loaddata db_export.json
```

**⏳ Thoda time lag sakta hai (size pe depend)**

**Expected Output:**
```
Installed xxxx object(s) from 1 fixture(s)
```

**✅ Matlab data aa gaya!**

---

## 🟢 STEP 6 — Superuser Verify/Create karo

### Option A: Create New Superuser

```bash
railway run python manage.py createsuperuser
```

**Enter करें:**
- Username
- Email
- Password

### Option B: Agar Pehle se Data me Admin tha

1. Login try karo: `https://your-app.up.railway.app/users/login/`
2. `/admin/` open karo: `https://your-app.up.railway.app/admin/`

---

## 🟢 STEP 7 — PostgreSQL UI me Verify

**Railway Dashboard में:**

1. **Postgres** service पर click करें
2. **"Database"** tab → **"Data"** tab
3. **Ab tables dikhni chahiye:**
   - `auth_user`
   - `users_user`
   - `orders_order`
   - etc.

**✅ Database properly setup ho gaya!**

---

## 🟢 STEP 8 — Cleanup (Optional)

**Import ke baad export file ko delete kar do:**

```bash
# Local se delete
rm db_export.json

# Git se remove (अगर push kiya tha)
git rm db_export.json
git commit -m "remove: db export file after import"
git push
```

---

## 📋 Complete Checklist:

- [ ] Local database export kiya (`db_export.json`)
- [ ] Railway web service me `DATABASE_URL` confirm kiya
- [ ] Railway par migrations run kiye
- [ ] Export file Railway me upload kiya (git push)
- [ ] Railway par data import kiya
- [ ] Superuser create/verify kiya
- [ ] PostgreSQL UI me tables verify kiye
- [ ] Export file cleanup kiya (optional)

---

## 🚀 Quick Commands Summary:

```bash
# 1. Local Export
python manage.py dumpdata --exclude contenttypes --exclude auth.permission --exclude sessions --natural-foreign --natural-primary --indent 2 > db_export.json

# 2. Git Push (temporary)
git add db_export.json
git commit -m "temp: add db export for Railway import"
git push

# 3. Railway Migrations
railway run python manage.py migrate

# 4. Railway Import
railway run python manage.py loaddata db_export.json

# 5. Create Superuser
railway run python manage.py createsuperuser

# 6. Cleanup (after import)
git rm db_export.json
git commit -m "remove: db export file after import"
git push
```

---

## ⚠️ Important Notes:

1. **Export file sensitive data contain karti hai** - GitHub me push karne se pehle socho
2. **Migrations pehle run karo** - Import se pehle zaroori hai
3. **DATABASE_URL confirm karo** - Web service me properly set hona chahiye
4. **Import ke baad cleanup karo** - Export file delete kar do

---

**Database migration complete होने के बाद, आपका app fully functional हो जाएगा!** 🎉


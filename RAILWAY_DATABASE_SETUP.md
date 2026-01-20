# Railway Database Setup Guide (हिंदी में)

## समस्या (Problem)
आपको Railway पर यह error मिल रहा है:
```
WARNING: No DATABASE_URL environment variable set
ERROR: settings.DATABASES is improperly configured
```

## समाधान (Solution)

### Step 1: Railway Dashboard में Database Add करें

1. **Railway Dashboard खोलें**: https://railway.app
2. अपने project में जाएं: **Atlas-crm-python-backend**
3. **"+ New"** button पर click करें
4. **"Database"** select करें
5. **"Add PostgreSQL"** select करें

या Terminal में:
```bash
railway add --database postgresql
```

### Step 2: DATABASE_URL Variable Check करें

Railway automatically `DATABASE_URL` set कर देता है, लेकिन verify करें:

1. Railway Dashboard में अपने **web** service पर click करें
2. **"Variables"** tab पर जाएं
3. देखें कि `DATABASE_URL` variable है या नहीं
4. अगर नहीं है, तो:
   - **"+ New Variable"** click करें
   - Name: `DATABASE_URL`
   - Value: अपने PostgreSQL service का connection string

### Step 3: Database Service से DATABASE_URL Copy करें

अगर आपने अलग से PostgreSQL service बनाया है:

1. PostgreSQL service पर click करें
2. **"Variables"** tab में जाएं
3. `DATABASE_URL` variable को copy करें
4. अपने **web** service के Variables में paste करें

या Railway automatically करता है अगर services linked हैं।

### Step 4: Redeploy करें

Database add करने के बाद:
1. Railway automatically redeploy करेगा
2. या manually **"Redeploy"** button click करें
3. Logs check करें - अब error नहीं आना चाहिए

---

## Database Import करने के लिए

अगर आपको local database का data Railway पर import करना है:

### Option 1: Django dumpdata/loaddata (Recommended)

**Local से Export:**
```bash
python export_database.py
```

**Railway पर Import:**
```bash
railway run python manage.py loaddata database_exports/atlas_crm_export_YYYYMMDD_HHMMSS.json
```

### Option 2: PostgreSQL pg_dump (अगर PostgreSQL use कर रहे हैं)

**Local से Export:**
```bash
pg_dump -h localhost -U atlas_user -d atlas_crm > atlas_backup.sql
```

**Railway पर Import:**
```bash
# Railway database URL get करें
railway variables get DATABASE_URL

# Import करें
psql $DATABASE_URL < atlas_backup.sql
```

---

## Quick Fix Commands

```bash
# 1. Railway CLI install (अगर नहीं है)
npm install -g @railway/cli

# 2. Login
railway login

# 3. Project link करें
railway link

# 4. PostgreSQL database add करें
railway add --database postgresql

# 5. Variables check करें
railway variables

# 6. Migrations run करें
railway run python manage.py migrate

# 7. Superuser create करें
railway run python manage.py createsuperuser
```

---

## Important Notes

1. ✅ Railway automatically `DATABASE_URL` set करता है जब आप PostgreSQL add करते हैं
2. ✅ Settings.py अब fixed है - fallback database configuration है
3. ✅ अगर `DATABASE_URL` नहीं मिलता, तो SQLite use होगा (local development के लिए)
4. ⚠️ Production में हमेशा PostgreSQL use करें

---

## Troubleshooting

### अगर अभी भी error आ रहा है:

1. **Variables check करें:**
   ```bash
   railway variables
   ```
   `DATABASE_URL` होना चाहिए

2. **Service restart करें:**
   - Railway Dashboard में service पर जाएं
   - **"Redeploy"** click करें

3. **Logs check करें:**
   ```bash
   railway logs
   ```
   देखें कि database connect हो रहा है या नहीं

4. **Database service check करें:**
   - PostgreSQL service "Online" होना चाहिए
   - Variables में `DATABASE_URL` होना चाहिए

---

**Database setup complete होने के बाद, आपका app Railway पर properly काम करेगा!** 🚀


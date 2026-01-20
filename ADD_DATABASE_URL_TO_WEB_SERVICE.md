# Web Service में DATABASE_URL Add करें

## ✅ PostgreSQL Database Ready!
आपका PostgreSQL database Railway पर ready है।

**Connection String:**
```
postgresql://postgres:APILoMaKLaigOsLSRonwfEsLvqXetmUM@postgres.railway.internal:5432/railway
```

---

## 🚀 अब Web Service में DATABASE_URL Add करें:

### Step 1: Web Service के Variables में जाएं

1. Railway Dashboard में अपने **"web"** service पर click करें
2. **"Variables"** tab पर click करें

### Step 2: DATABASE_URL Variable Add करें

**Option A: Variable Reference Use करें (Recommended):**

1. **"+ New Variable"** button click करें
2. Name: `DATABASE_URL`
3. Value में: `${{Postgres.DATABASE_URL}}` लिखें
   - यह automatically PostgreSQL service का `DATABASE_URL` use करेगा
4. **"Add"** click करें

**Option B: Direct Connection String (अगर Option A काम न करे):**

1. **"+ New Variable"** button click करें
2. Name: `DATABASE_URL`
3. Value: `postgresql://postgres:APILoMaKLaigOsLSRonwfEsLvqXetmUM@postgres.railway.internal:5432/railway`
4. **"Add"** click करें

**⚠️ Note:** Internal URL (`postgres.railway.internal`) सिर्फ same project के services के लिए काम करता है। अगर external connection चाहिए, तो `DATABASE_PUBLIC_URL` use करें।

---

### Step 3: Redeploy करें

1. Web service पर जाएं
2. **"Deployments"** tab में जाएं
3. **"Redeploy"** button click करें
4. या Railway automatically redeploy करेगा

---

### Step 4: Migrations Run करें

Terminal में:

```bash
# 1. Login (अगर नहीं है)
railway login

# 2. Project link करें
railway link

# 3. Migrations run करें
railway run python manage.py migrate

# 4. Superuser create करें
railway run python manage.py createsuperuser
```

---

## 📋 Quick Checklist:

- [ ] Web service के Variables tab में गए
- [ ] `DATABASE_URL` variable add किया
- [ ] Value: `${{Postgres.DATABASE_URL}}` या direct connection string
- [ ] Redeploy किया
- [ ] Migrations run किए
- [ ] Superuser create किया

---

## ⚠️ Important Notes:

1. **Variable Reference (`${{Postgres.DATABASE_URL}}`) use करना better है** क्योंकि:
   - Automatically update होगा अगर database credentials change हों
   - More secure है
   - Railway recommended approach है

2. **अगर Internal URL काम न करे**, तो:
   - PostgreSQL service के Variables में `DATABASE_PUBLIC_URL` check करें
   - उसे use करें (external connection के लिए)

3. **Database में tables नहीं हैं** - यह normal है
   - Migrations run करने के बाद tables create होंगे

---

## 🎯 After Setup:

✅ `DATABASE_URL` variable set होगा  
✅ Migrations run होंगे  
✅ Database tables create होंगे  
✅ App properly काम करेगा  
✅ Login काम करेगा  

---

**DATABASE_URL add करने के बाद, migrations run करें और app ready हो जाएगा!** 🚀


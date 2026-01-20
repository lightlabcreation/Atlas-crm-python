# Railway पर Database Add करने के Steps (हिंदी में)

## ✅ Git Push Complete!
सभी changes git में push हो गए हैं।

---

## 🚀 अब Railway पर Database Add करें:

### Method 1: Railway Dashboard से (सबसे आसान) ⭐

**Step-by-Step:**

1. **Railway Dashboard खोलें:**
   - https://railway.app पर जाएं
   - Login करें

2. **अपने Project में जाएं:**
   - "Atlas-crm-python-backend" project select करें

3. **Database Add करें:**
   - Top right में **"+ New"** button click करें
   - **"Database"** select करें
   - **"Add PostgreSQL"** click करें

4. **Wait करें:**
   - 1-2 minutes wait करें
   - Railway automatically:
     - PostgreSQL database create करेगा
     - `DATABASE_URL` variable set कर देगा
     - Service को link कर देगा

5. **Verify करें:**
   - "web" service पर click करें
   - "Variables" tab में जाएं
   - `DATABASE_URL` variable check करें

6. **Migrations Run करें:**
   - Terminal में:
     ```bash
     railway run python manage.py migrate
     ```

7. **Superuser Create करें:**
   ```bash
   railway run python manage.py createsuperuser
   ```

---

### Method 2: Railway CLI से (Terminal)

**अगर आप Terminal use करना prefer करते हैं:**

```bash
# 1. Login (अगर नहीं है)
railway login

# 2. Project link करें
railway link

# 3. PostgreSQL database add करें
railway add --database postgresql

# 4. Variables check करें
railway variables

# 5. Migrations run करें
railway run python manage.py migrate

# 6. Superuser create करें
railway run python manage.py createsuperuser
```

---

## 📋 Checklist:

- [ ] Railway Dashboard में PostgreSQL database add किया
- [ ] `DATABASE_URL` variable check किया
- [ ] Migrations run किए
- [ ] Superuser create किया
- [ ] App test किया (login करके)

---

## ⚠️ Important:

1. **Database add करने के बाद Railway automatically redeploy करेगा**
2. **2-3 minutes wait करें** - Database setup होने के लिए
3. **अगर error आए**, तो:
   - Check करें कि PostgreSQL service "Online" है
   - Check करें कि `DATABASE_URL` variable set है
   - Logs check करें

---

## 🎯 After Database Setup:

✅ App properly काम करेगा  
✅ Login काम करेगा  
✅ सभी database operations काम करेंगे  
✅ Data save/load होगा  

---

**Database add करने के बाद, आपका app fully functional हो जाएगा!** 🎉


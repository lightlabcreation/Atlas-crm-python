# Railway Deployment - Manual Configuration Required

## Current Status

**Project**: charming-possibility (ID: 3781876d-0f00-478c-b419-0ec4b0c7819a)
**Service**: atlas-crm
**Current Deployment**: Kiaan WMS (Next.js frontend)
**Expected**: Atlas CRM (Django backend)

**URL**: https://atlas-crm-production.up.railway.app

---

## Problem Identified

The Railway service "atlas-crm" is configured to build and run a Next.js application (Kiaan WMS), not the Django backend (Atlas CRM).

When we deployed the Django code, Railway used its existing build configuration which expects a Next.js app, so the Django application was not built or started correctly.

---

## Why This Happened

Railway services have build configurations that determine:
1. What to build (Node.js vs Python)
2. How to build (npm install vs pip install)
3. How to start (next start vs gunicorn)

The "atlas-crm" service has a configuration for Next.js, likely:
- **Start Command**: `next start` or `npm start`
- **Build Command**: `npm run build`
- **Root Directory**: Points to a frontend directory

---

## Solution: Reconfigure the Service

You need to manually update the Railway service configuration via the dashboard.

### Option 1: Update Existing Service (Recommended)

#### Step 1: Access Service Settings
1. Go to https://railway.app/project/3781876d-0f00-478c-b419-0ec4b0c7819a
2. Click on the "atlas-crm" service
3. Go to **Settings** tab

#### Step 2: Configure Build Settings
Scroll to **Build** section and update:

**Root Directory**:
```
/
```
*(or leave blank if repo root has Django code)*

**Build Command**:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command**:
```
gunicorn crm_fulfillment.wsgi --bind 0.0.0.0:$PORT --workers 3 --timeout 120
```

#### Step 3: Set Environment Variables
Go to **Variables** tab and ensure these are set:

```bash
SECRET_KEY=7c#5pmt&59lv#w*dhmf5vv57rm1+b7t=m1+u1jcttm7z0qy*%7
DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}
DJANGO_ALLOWED_HOSTS=.up.railway.app,.railway.app
```

#### Step 4: Redeploy
- Click **Deploy** → **Redeploy**
- Or make a dummy commit and push to trigger deployment

---

### Option 2: Create Separate Backend Service

If you want to keep the Next.js frontend, create a new service for Django:

#### Step 1: Create New Service
1. In Railway dashboard, click **+ New**
2. Select "Empty Service"
3. Name it: `atlas-crm-backend`

#### Step 2: Connect Source
- Link to your GitHub repo
- Or upload code directly

#### Step 3: Configure Build
Set these in Settings:

**Build Command**:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command**:
```
gunicorn crm_fulfillment.wsgi --bind 0.0.0.0:$PORT --workers 3 --timeout 120
```

#### Step 4: Set Variables
```bash
SECRET_KEY=7c#5pmt&59lv#w*dhmf5vv57rm1+b7t=m1+u1jcttm7z0qy*%7
DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}
DJANGO_ALLOWED_HOSTS=.up.railway.app,.railway.app
```

#### Step 5: Deploy
- Service will auto-deploy
- Generate domain: Settings → Networking → Generate Domain

---

## Using CLI (After Manual Config)

Once the service is properly configured via dashboard, you can use CLI:

```bash
# Deploy from Django directory
cd /root/new-python-code

# Deploy to the configured service
RAILWAY_TOKEN="cbe816b4-cd55-4d6b-9c3c-f3535da1d131" railway up --service atlas-crm

# Or if you created new service:
RAILWAY_TOKEN="cbe816b4-cd55-4d6b-9c3c-f3535da1d131" railway up --service atlas-crm-backend
```

---

## Verification Steps

After reconfiguring, verify the deployment:

### 1. Check Build Logs
Look for:
```
Installing collected packages: Django, gunicorn, ...
Successfully installed Django-5.x.x
```

### 2. Check Start Logs
Look for:
```
Starting gunicorn...
Listening at: http://0.0.0.0:8000
```

### 3. Test Django Admin
```bash
curl https://atlas-crm-production.up.railway.app/admin/
```

Should return Django admin page HTML, not Next.js content.

### 4. Test API Endpoint
```bash
curl https://atlas-crm-production.up.railway.app/api/
```

---

## Post-Deployment Tasks

Once Django is properly deployed:

### 1. Run Migrations
```bash
RAILWAY_TOKEN="cbe816b4-cd55-4d6b-9c3c-f3535da1d131" railway run --service atlas-crm python manage.py migrate
```

### 2. Create Superuser
```bash
RAILWAY_TOKEN="cbe816b4-cd55-4d6b-9c3c-f3535da1d131" railway run --service atlas-crm python manage.py createsuperuser
```

### 3. Test Login
Visit: https://atlas-crm-production.up.railway.app/admin/
Login with superuser credentials

---

## Current Files Ready for Deployment

All Django deployment files are in `/root/new-python-code`:

✅ **Procfile** - Railway process definition
```
web: gunicorn crm_fulfillment.wsgi --bind 0.0.0.0:$PORT --workers 3 --timeout 120
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
```

✅ **railway.json** - Railway configuration
✅ **nixpacks.toml** - Build environment
✅ **runtime.txt** - Python 3.12.3
✅ **requirements.txt** - All dependencies (fixed)
✅ **settings.py** - Railway-ready with DATABASE_URL support

---

## Why Can't We Fix This with CLI?

**Project tokens** (`RAILWAY_TOKEN`) can only:
- Deploy code
- View logs
- Set variables

They **cannot**:
- Modify service build configuration
- Change start commands
- Update root directory
- Create new services

These operations require:
- **Account token** with full permissions
- **Dashboard access** (browser login)

---

## Quick Dashboard Access

**Project URL**:
```
https://railway.app/project/3781876d-0f00-478c-b419-0ec4b0c7819a
```

**Login** at: https://railway.app/login

---

## Expected Build Output (After Fix)

Once properly configured, you should see:

```
Building...
[nixpacks] Detecting Python application
[nixpacks] Using Python 3.12.3
[nixpacks] Installing dependencies from requirements.txt
[nixpacks] Collecting Django>=5.0.0
[nixpacks] Collecting gunicorn>=21.2.0
[nixpacks] Collecting psycopg2-binary>=2.9.9
...
[nixpacks] Successfully installed Django-5.x.x
[nixpacks] Collecting static files...
[nixpacks] 150 static files copied

Starting...
[gunicorn] Starting gunicorn 21.2.0
[gunicorn] Listening at: http://0.0.0.0:8000 (PID: 1)
[gunicorn] Using worker: sync
[gunicorn] Booting worker with pid: 7
[gunicorn] Booting worker with pid: 8
[gunicorn] Booting worker with pid: 9
```

---

## Summary

**Action Required**: Manual service configuration via Railway dashboard

**Steps**:
1. Login to Railway dashboard
2. Access service settings
3. Update build/start commands to Django
4. Redeploy service

**Estimated Time**: 5-10 minutes

**Result**: Django backend running at https://atlas-crm-production.up.railway.app

---

## Support Files Created

- ✅ `RAILWAY_DEPLOYMENT_GUIDE.md` - Comprehensive deployment guide
- ✅ `RAILWAY_DEPLOYMENT_COMMANDS.md` - CLI commands reference
- ✅ `RAILWAY_SETUP_COMPLETE_GUIDE.md` - Multi-service setup
- ✅ `RAILWAY_MANUAL_FIX_REQUIRED.md` - This document
- ✅ `deploy-to-railway.sh` - Automated deployment script

Total Documentation: 1,500+ lines

---

**Status**: ⏳ **Awaiting Manual Configuration**

**Next Step**: Access Railway dashboard and update service configuration

**Project Token Available**: `cbe816b4-cd55-4d6b-9c3c-f3535da1d131` (for CLI after fix)

---

*Generated: December 5, 2025*
*Atlas CRM - Ready for deployment after service configuration*

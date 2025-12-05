# Atlas CRM - Complete Railway Setup Guide

## Current Situation

**Project ID**: `3781876d-0f00-478c-b419-0ec4b0c7819a`
**Project Token**: `cbe816b4-cd55-4d6b-9c3c-f3535da1d131`
**Current Service**: `atlas-crm` (running Kiaan WMS Next.js app)
**Current URL**: https://atlas-crm-production.up.railway.app

## Problem Identified

The "atlas-crm" service is currently running a Next.js frontend (Kiaan WMS), not the Atlas CRM Django backend. We need to set up proper services for both backend and frontend.

---

## Solution: Set Up Multiple Services

Railway projects can have multiple services. You need to create separate services for:
1. **Backend Service** - Django (Atlas CRM API)
2. **Frontend Service** - Next.js (if you have one)
3. **Database** - PostgreSQL (already exists)

---

## Step-by-Step Setup

### Option 1: Via Railway Dashboard (Recommended)

#### 1. Login to Railway Dashboard
```
https://railway.app/project/3781876d-0f00-478c-b419-0ec4b0c7819a
```

#### 2. Create New Service for Django Backend

1. Click "+ New" → "Empty Service"
2. Name it: `atlas-crm-backend`
3. Go to Settings → Source → Connect to GitHub repo or deploy from local
4. Set Root Directory to `/` (or where your Django code is)
5. Configure Build Settings:
   - Builder: **Dockerfile** or **Nixpacks**
   - Build Command: (leave empty, use Dockerfile/Procfile)
   - Start Command: `gunicorn crm_fulfillment.wsgi --bind 0.0.0.0:$PORT --workers 3`

#### 3. Set Environment Variables for Backend

Go to Variables tab and add:

```bash
# Required
SECRET_KEY=7c#5pmt&59lv#w*dhmf5vv57rm1+b7t=m1+u1jcttm7z0qy*%7
DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Reference existing DB

# Optional
DJANGO_ALLOWED_HOSTS=.up.railway.app,.railway.app
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
```

#### 4. Deploy Backend

- Click "Deploy" or wait for auto-deploy
- Railway will build using your Dockerfile or Procfile
- Monitor logs in the Deployments tab

#### 5. Generate Domain

- Go to Settings → Networking
- Click "Generate Domain"
- You'll get: `https://atlas-crm-backend-production.up.railway.app`

### Option 2: Via CLI (After Browser Login)

#### 1. Login First (Browser Required)
```bash
railway login
```

#### 2. Link to Project
```bash
cd /root/new-python-code
railway link -p 3781876d-0f00-478c-b419-0ec4b0c7819a
```

#### 3. Create New Service
```bash
# Railway CLI doesn't support creating services directly
# You must use the dashboard to create the service first
# Then deploy to it:
railway up --service atlas-crm-backend
```

---

## Understanding Railway Services

### Current Services in Your Project:

1. **atlas-crm** (Current)
   - Type: Next.js Frontend
   - Running: Kiaan WMS
   - URL: https://atlas-crm-production.up.railway.app

2. **Postgres** (Database)
   - Already configured
   - DATABASE_URL available to all services

### What You Need:

1. **atlas-crm-backend** (New)
   - Type: Django API
   - Source: `/root/new-python-code`
   - Start: `gunicorn crm_fulfillment.wsgi`

2. **atlas-crm-frontend** (New - if needed)
   - Type: Next.js
   - Source: Your frontend repo
   - Start: `next start`

---

## Deployment Files Ready

All deployment files are already in `/root/new-python-code`:

✅ **Procfile** - Process definitions
✅ **Dockerfile** - Container build (if exists)
✅ **railway.json** - Railway configuration
✅ **nixpacks.toml** - Build settings
✅ **runtime.txt** - Python 3.12.3
✅ **requirements.txt** - Dependencies (fixed)

---

## Environment Variables Reference

### Backend (Django) - Required:

| Variable | Value | Purpose |
|----------|-------|---------|
| `SECRET_KEY` | `7c#5pmt&59lv#w*dhmf5vv57rm1+b7t=m1+u1jcttm7z0qy*%7` | Django secret |
| `DEBUG` | `False` | Production mode |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | PostgreSQL connection |

### Backend (Django) - Optional:

| Variable | Value | Purpose |
|----------|-------|---------|
| `DJANGO_ALLOWED_HOSTS` | `.up.railway.app,.railway.app` | Allowed domains |
| `EMAIL_HOST` | `smtp.hostinger.com` | Email server |
| `EMAIL_PORT` | `465` | Email port |
| `EMAIL_USE_SSL` | `True` | Use SSL for email |
| `EMAIL_HOST_USER` | `your-email@domain.com` | Email username |
| `EMAIL_HOST_PASSWORD` | `your-password` | Email password |
| `CLOUDINARY_CLOUD_NAME` | `your-cloud` | File storage |
| `CLOUDINARY_API_KEY` | `your-key` | Cloudinary key |
| `CLOUDINARY_API_SECRET` | `your-secret` | Cloudinary secret |

---

## Service Communication

Services can communicate using Railway's private networking:

```bash
# Backend can be accessed by frontend via:
https://atlas-crm-backend.railway.internal

# Or use environment variable references:
BACKEND_URL=${{atlas-crm-backend.RAILWAY_PUBLIC_DOMAIN}}
```

---

## Project Token Limitations

**What You CAN Do with Project Token:**
- ✅ Deploy code (`railway up`)
- ✅ View logs (`railway logs`)
- ✅ Set variables (`railway variables --set`)
- ✅ Check domain (`railway domain`)

**What You CANNOT Do:**
- ❌ Create new services (requires browser login)
- ❌ Modify service settings
- ❌ Delete services
- ❌ Manage team/workspace

**Solution:** For initial setup, you need to login via browser once:
```bash
railway login  # Opens browser
```

---

## Quick Setup Commands (After Browser Login)

```bash
# 1. Login (one-time, opens browser)
railway login

# 2. Link to project
cd /root/new-python-code
railway link -p 3781876d-0f00-478c-b419-0ec4b0c7819a

# 3. Create service via dashboard (cannot do via CLI)
# Visit: https://railway.app/project/3781876d-0f00-478c-b419-0ec4b0c7819a
# Click: + New → Empty Service → Name: atlas-crm-backend

# 4. Deploy to new service
railway up --service atlas-crm-backend

# 5. Set variables
railway variables --service atlas-crm-backend \
  --set "SECRET_KEY=7c#5pmt&59lv#w*dhmf5vv57rm1+b7t=m1+u1jcttm7z0qy*%7" \
  --set "DEBUG=False"

# 6. Generate domain
railway domain --service atlas-crm-backend

# 7. Run migrations
railway run --service atlas-crm-backend python manage.py migrate

# 8. Create superuser
railway run --service atlas-crm-backend python manage.py createsuperuser
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│         Railway Project: charming-possibility         │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┐
        │           │           │           │
   ┌────▼────┐ ┌───▼────┐ ┌────▼────┐ ┌────▼────┐
   │  Frontend  │ │ Backend  │ │ Database │ │  Redis   │
   │  (Next.js) │ │ (Django) │ │ (Postgres)│ │ (Optional)│
   └──────────┘ └─────────┘ └─────────┘ └─────────┘
        │             │            │
        │             │            │
   Port 3000     Port 8000    Port 5432
```

---

## Troubleshooting

### Issue: Deployment shows Next.js instead of Django

**Cause:** Service is configured for the wrong source/root directory

**Fix:**
1. Go to Railway Dashboard
2. Service Settings → Source
3. Check Root Directory is correct
4. Verify it's pulling from Django backend repo

### Issue: Build fails with "gunicorn: command not found"

**Cause:** Dependencies not installed or wrong start command

**Fix:**
1. Verify `requirements.txt` includes `gunicorn>=21.2.0`
2. Check Procfile has correct start command
3. Ensure build completed successfully

### Issue: Database connection error

**Cause:** DATABASE_URL not set or incorrect

**Fix:**
1. Verify Postgres service exists in project
2. Set `DATABASE_URL=${{Postgres.DATABASE_URL}}` in variables
3. Check database is running

### Issue: 400 Bad Request - Invalid Host Header

**Cause:** Domain not in ALLOWED_HOSTS

**Fix:**
```bash
railway variables --service atlas-crm-backend \
  --set "DJANGO_ALLOWED_HOSTS=.up.railway.app,.railway.app"
```

---

## Testing Deployment

```bash
# Test backend API
curl https://atlas-crm-backend-production.up.railway.app/admin/

# Test with authentication
curl -X POST https://atlas-crm-backend-production.up.railway.app/users/login/ \
  -d "username=admin&password=yourpassword"

# Check health
curl https://atlas-crm-backend-production.up.railway.app/health/ || echo "No health endpoint"
```

---

##Custom Domain Setup

### Add Custom Domain to Backend:

1. Go to Service Settings → Networking
2. Click "Custom Domain"
3. Add: `api.atlas.alexandratechlab.com`
4. Configure DNS:
   ```
   Type: CNAME
   Name: api.atlas
   Value: atlas-crm-backend-production.up.railway.app
   ```

---

## Cost Estimate

**Current Usage:**
- Frontend Service: ~$10-15/month
- Backend Service: ~$10-15/month
- PostgreSQL: Included in compute
- Total: ~$20-30/month

**Railway Pricing:**
- Hobby: $5/month + usage
- Usage: $0.000463/minute (~$20/month for 24/7)

---

## Next Steps

1. **Browser Login** (Required once):
   ```bash
   railway login
   ```

2. **Create Backend Service** (via Dashboard):
   - Visit https://railway.app/project/3781876d-0f00-478c-b419-0ec4b0c7819a
   - Create new service named `atlas-crm-backend`

3. **Deploy Backend**:
   ```bash
   railway up --service atlas-crm-backend
   ```

4. **Configure Variables** (see Environment Variables section above)

5. **Run Migrations & Create Superuser**:
   ```bash
   railway run --service atlas-crm-backend python manage.py migrate
   railway run --service atlas-crm-backend python manage.py createsuperuser
   ```

6. **Test Deployment**:
   ```bash
   railway domain --service atlas-crm-backend
   curl <url>/admin/
   ```

---

## Summary

**Status**: ✅ Code ready, needs service setup

**What's Done**:
- ✅ Requirements.txt fixed
- ✅ Deployment files created
- ✅ Environment variables prepared
- ✅ Database exists in project
- ✅ Domain configuration ready

**What's Needed**:
- ⏳ Browser login to Railway
- ⏳ Create `atlas-crm-backend` service via dashboard
- ⏳ Deploy Django backend to new service
- ⏳ Run migrations
- ⏳ Create superuser

**Estimated Time**: 10-15 minutes

---

**Project**: Atlas CRM
**Railway Project ID**: 3781876d-0f00-478c-b419-0ec4b0c7819a
**Generated**: December 5, 2025
**Status**: Ready for manual service creation

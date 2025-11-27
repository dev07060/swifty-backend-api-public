# Quick Start Guide 🚀

Welcome! This guide will help you deploy your Swifty Backend API quickly.

## Choose Your Path

### Path 1: Test Locally First (Recommended for Development)

**Best for:** Learning, development, testing before production

1. **Install Docker Desktop**
   - Download: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Configure environment**
   ```bash
   cd /Users/dev_bh/Desktop/works/python-api/swifty-backend-api
   cp .env.example .env
   nano .env  # Add your GEMINI_API_KEY
   ```

3. **Start everything**
   ```bash
   docker-compose up
   ```

4. **Test your API**
   - Open browser: http://localhost:8080/docs
   - Try creating a user and logging exercises/food

5. **Read detailed guide:** [docs/LOCAL_DEVELOPMENT.md](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/docs/LOCAL_DEVELOPMENT.md)

---

### Path 2: Deploy Directly to GCP (Production)

**Best for:** Going straight to production

1. **Install gcloud CLI**
   ```bash
   brew install --cask google-cloud-sdk
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Follow deployment guide**
   - Open: [docs/DEPLOYMENT.md](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/docs/DEPLOYMENT.md)
   - Follow step-by-step instructions
   - Estimated time: 30-45 minutes

3. **Quick deployment steps:**
   ```bash
   # Set your project
   export PROJECT_ID="your-project-id"
   export REGION="us-central1"
   
   # Create project and enable APIs
   gcloud projects create $PROJECT_ID
   gcloud config set project $PROJECT_ID
   gcloud services enable run.googleapis.com sql-component.googleapis.com
   
   # Create Cloud SQL instance
   gcloud sql instances create swifty-postgres \
     --database-version=POSTGRES_16 \
     --tier=db-f1-micro \
     --region=$REGION
   
   # Deploy with automated script
   ./deploy.sh production
   ```

---

## What You Have Now

✅ **Database Schema** - Ready for PostgreSQL 16  
✅ **Docker Setup** - For local testing  
✅ **GCP Configuration** - Cloud Run + Cloud SQL  
✅ **CORS Settings** - Configured for tossmini.com  
✅ **Documentation** - Complete guides  
✅ **Deployment Scripts** - Automated deployment  

## Files to Review

| File | What to Read |
|------|-------------|
| [docs/DEPLOYMENT.md](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/docs/DEPLOYMENT.md) | **Start here for GCP deployment** |
| [docs/LOCAL_DEVELOPMENT.md](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/docs/LOCAL_DEVELOPMENT.md) | Local testing with Docker |
| [database/schema.sql](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/database/schema.sql) | Your database structure |
| [.env.production.example](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/.env.production.example) | Environment variables needed |

## Important: Your CORS Configuration

Your API is configured to accept requests from:
- `https://app-swifty-healthy.apps.tossmini.com` (production)
- `https://app-swifty-healthy.private-apps.tossmini.com` (staging/debug)

This is set in `.env.production.example` and `cloudbuild.yaml`.

## Estimated Costs (GCP)

**Monthly:** ~$16-32 for moderate usage
- Cloud Run: $5-15
- Cloud SQL: $10-15  
- Storage/Egress: $1-2

**Free Tier Benefits:**
- Cloud Run: 2M requests/month free
- New users: $300 free credits

## Need Help?

1. **Local issues?** → [docs/LOCAL_DEVELOPMENT.md](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/docs/LOCAL_DEVELOPMENT.md) → Troubleshooting section
2. **GCP deployment issues?** → [docs/DEPLOYMENT.md](file:///Users/dev_bh/Desktop/works/python-api/swifty-backend-api/docs/DEPLOYMENT.md) → Troubleshooting section
3. **Database questions?** → Check `database/schema.sql` for table structure

## Next Action

**If you want to test locally:**
```bash
# Install Docker, then:
docker-compose up
open http://localhost:8080/docs
```

**If you want to deploy to production:**
```bash
# Read the deployment guide first:
open docs/DEPLOYMENT.md
# Then follow the steps
```

---

Good luck! Your backend is ready to deploy. 🎉

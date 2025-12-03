# Cloud Run Deployment Guide

## Prerequisites

1. **GCP Account & Project**
   - Create a GCP project at https://console.cloud.google.com
   - Note your Project ID

2. **Install gcloud CLI**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

3. **Authenticate**
   ```bash
   gcloud auth login
   gcloud auth configure-docker
   ```

## Quick Deploy

### 1. Update Configuration

Edit `deploy-cloud-run.sh`:
```bash
PROJECT_ID="your-actual-project-id"  # Change this!
```

### 2. Prepare Environment Variables

Make sure `.env.production` has all required values:
```bash
# Database (Cloud SQL or external)
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname

# Gemini API
GEMINI_API_KEY=your-key-here

# Toss Cert Auth
TOSS_CERT_CLIENT_ID=your-toss-client-id
TOSS_CERT_CLIENT_SECRET=your-toss-client-secret

# Server Config
MAX_IMAGE_SIZE_MB=10
LOG_LEVEL=INFO
ENVIRONMENT=production
CORS_ORIGINS=*
```

### 3. Deploy

```bash
cd swifty-backend-api-public
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
```

### 4. Update Mobile App

After deployment, you'll get a URL like:
```
https://swifty-backend-api-xxxxx-an.a.run.app
```

Update your mobile app's `.env`:
```bash
API_BASE_URL=https://swifty-backend-api-xxxxx-an.a.run.app
```

Then rebuild your React Native app.

## Manual Deployment

If the script doesn't work, deploy manually:

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/swifty-backend-api

# Deploy
gcloud run deploy swifty-backend-api \
  --image gcr.io/YOUR_PROJECT_ID/swifty-backend-api \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-env-vars "TOSS_CERT_CLIENT_ID=xxx,TOSS_CERT_CLIENT_SECRET=xxx,DATABASE_URL=xxx" \
  --memory 512Mi \
  --port 8080
```

## Testing

Test your deployed API:

```bash
# Health check
curl https://your-service-url.run.app/docs

# Test Toss auth endpoint
curl -X POST https://your-service-url.run.app/api/toss-auth/request
```

## Troubleshooting

**Build fails:**
- Check Dockerfile syntax
- Ensure all dependencies in requirements.txt
- Check build logs: `gcloud builds list`

**Deploy fails:**
- Check environment variables are set
- Verify service account permissions
- Check logs: `gcloud run logs read --service swifty-backend-api`

**502 errors:**
- Check database connection
- Verify PORT environment variable usage
- Check application logs

## Database Setup (Cloud SQL)

If using Cloud SQL:

```bash
# Create instance
gcloud sql instances create swifty-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3

# Create database
gcloud sql databases create swifty_app --instance=swifty-db

# Set password
gcloud sql users set-password postgres \
  --instance=swifty-db \
  --password=YOUR_PASSWORD

# Get connection name
gcloud sql instances describe swifty-db --format='value(connectionName)'

# Update DATABASE_URL in .env.production
# Use Cloud SQL Proxy or private IP
```

## Cost Optimization

- **Start with:** 512Mi memory, 1 CPU, 0 min instances
- **Increase if needed:** Monitor performance in Cloud Console
- **Min instances:** Set to 0 for development, 1+ for production

## Next Steps

After deployment:
1. ✅ Test endpoints with curl
2. ✅ Update mobile app config
3. ✅ Rebuild and test mobile app
4. ✅ Monitor logs in GCP Console

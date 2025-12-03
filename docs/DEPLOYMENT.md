# Deployment Guide: Google Cloud Platform

This guide walks you through deploying the Swifty Backend API to Google Cloud Platform using **Cloud Run** (for the API) and **Cloud SQL** (for PostgreSQL 16 database).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial GCP Setup](#initial-gcp-setup)
3. [Cloud SQL Setup (PostgreSQL 16)](#cloud-sql-setup)
4. [Secrets Manager Setup](#secrets-manager-setup)
5. [Cloud Run Deployment](#cloud-run-deployment)
6. [Domain Configuration](#domain-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- [ ] Google Cloud Platform account
- [ ] `gcloud` CLI installed ([Install guide](https://cloud.google.com/sdk/docs/install))
- [ ] Docker installed locally (for testing)
- [ ] Your Gemini API key
- [ ] Billing enabled on your GCP project

### Install gcloud CLI

```bash
# macOS
brew install --cask google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

---

## Initial GCP Setup

### 1. Create a New GCP Project

```bash
# Set your project ID (must be globally unique)
export PROJECT_ID="swifty-backend-prod"
export REGION="us-central1"  # Choose your preferred region

# Create the project
gcloud projects create $PROJECT_ID --name="Swifty Backend"

# Set as active project
gcloud config set project $PROJECT_ID
```

### 2. Enable Required APIs

```bash
# Enable necessary GCP services
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com
```

### 3. Set Default Region

```bash
gcloud config set run/region $REGION
gcloud config set compute/region $REGION
```

---

## Cloud SQL Setup

### 1. Create PostgreSQL 16 Instance

```bash
# Create Cloud SQL instance
gcloud sql instances create swifty-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=$REGION \
  --network=default \
  --no-assign-ip \
  --database-flags=max_connections=100

# Note: For production, consider a larger tier like db-custom-2-7680
```

> [!TIP]
> **Cost Optimization**: The `db-f1-micro` tier is the cheapest option (~$10/month). For production with higher traffic, upgrade to `db-g1-small` or `db-custom-*` tiers.

### 2. Create Database and User

```bash
# Set a secure root password
gcloud sql users set-password postgres \
  --instance=swifty-postgres \
  --password="YOUR_SECURE_ROOT_PASSWORD"

# Create application database
gcloud sql databases create swifty \
  --instance=swifty-postgres

# Create application user
gcloud sql users create swifty_user \
  --instance=swifty-postgres \
  --password="YOUR_SECURE_APP_PASSWORD"
```

> [!IMPORTANT]
> **Save these credentials securely!** You'll need them for Secrets Manager in the next step.

### 3. Initialize Database Schema

```bash
# Get your Cloud SQL connection name
gcloud sql instances describe swifty-postgres --format="value(connectionName)"
# Output example: PROJECT_ID:REGION:swifty-postgres

# Option A: Use Cloud SQL Proxy (recommended for initial setup)
# Download and run Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Start proxy (in a separate terminal)
./cloud-sql-proxy $PROJECT_ID:$REGION:swifty-postgres

# In another terminal, run the schema
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=swifty-prd
export DB_USER=swifty_user
export DB_PASSWORD="YOUR_SECURE_APP_PASSWORD"

# Execute schema
./database/init.sh

# Or manually with psql
psql -h localhost -p 5432 -U swifty_user -d swifty -f database/schema.sql
```

---

## Secrets Manager Setup

Store sensitive credentials in Google Secret Manager:

```bash
# 1. Create secret for database password
echo -n "YOUR_SECURE_APP_PASSWORD" | \
  gcloud secrets create swifty-db-password \
  --data-file=- \
  --replication-policy="automatic"

# 2. Create secret for Gemini API key
echo -n "YOUR_GEMINI_API_KEY" | \
  gcloud secrets create swifty-gemini-api-key \
  --data-file=- \
  --replication-policy="automatic"

# 3. Grant Cloud Run access to secrets
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding swifty-db-password \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding swifty-gemini-api-key \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Cloud Run Deployment

### Option 1: Manual Deployment (Quick Start)

```bash
# 1. Build and submit the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/swifty-api

# 2. Deploy to Cloud Run
gcloud run deploy swifty-api \
  --image gcr.io/$PROJECT_ID/swifty-api \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:$REGION:swifty-postgres \
  --set-env-vars "ENVIRONMENT=production,DB_HOST=/cloudsql/$PROJECT_ID:$REGION:swifty-postgres,DB_PORT=5432,DB_NAME=swifty,DB_USER=swifty_user,GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent,GEMINI_TIMEOUT=30,MAX_IMAGE_SIZE_MB=10,LOG_LEVEL=INFO,CORS_ORIGINS=https://app-swifty-healthy.apps.tossmini.com,https://app-swifty-healthy.private-apps.tossmini.com" \
  --set-secrets "DB_PASSWORD=swifty-db-password:latest,GEMINI_API_KEY=swifty-gemini-api-key:latest" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80
```

> [!NOTE]
> Your API will be available at: `https://swifty-api-XXXXXXXXXX-uc.a.run.app`

### Option 2: Using Cloud Build (Recommended for CI/CD)

```bash
# 1. Update cloudbuild.yaml substitutions
# Edit cloudbuild.yaml and replace:
# - YOUR_PROJECT_ID with your actual project ID
# - YOUR_REGION with your region

# 2. Submit build
gcloud builds submit --config cloudbuild.yaml
```

### Option 3: GitHub Actions (Automated CI/CD)

See `.github/workflows/deploy.yml` for automated deployment on git push.

---

## Verify Deployment

### 1. Test the API

```bash
# Get your Cloud Run URL
SERVICE_URL=$(gcloud run services describe swifty-api --region=$REGION --format="value(status.url)")

echo "API URL: $SERVICE_URL"

# Test the /docs endpoint
curl $SERVICE_URL/docs

# Test a simple endpoint (create a user first)
curl -X POST "$SERVICE_URL/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "userKey": "test_user_001",
    "gender": "male",
    "ageRange": "20-30"
  }'
```

### 2. Check Logs

```bash
# View recent logs
gcloud run services logs read swifty-api --region=$REGION --limit=50

# Stream logs in real-time
gcloud run services logs tail swifty-api --region=$REGION
```

### 3. Monitor Performance

Visit [Google Cloud Console > Cloud Run](https://console.cloud.google.com/run) to view:
- Request count
- Latency metrics
- Error rates
- Instance scaling

---

## Domain Configuration

### Map Custom Domain to Cloud Run

```bash
# 1. Verify domain ownership (if not already done)
gcloud domains verify app-swifty-healthy.apps.tossmini.com

# 2. Map domain to Cloud Run service
gcloud run domain-mappings create \
  --service swifty-api \
  --domain app-swifty-healthy.apps.tossmini.com \
  --region $REGION

# 3. Update DNS records
# Add the following records to your DNS provider (tossmini.com):
# Get the required DNS records:
gcloud run domain-mappings describe \
  --domain app-swifty-healthy.apps.tossmini.com \
  --region $REGION
```

> [!IMPORTANT]
> After mapping your domain, update the CORS_ORIGINS environment variable to include both domains:
> - `https://app-swifty-healthy.apps.tossmini.com` (production)
> - `https://app-swifty-healthy.private-apps.tossmini.com` (staging)

---

## Monitoring & Logging

### Set Up Alerts

1. Navigate to **Cloud Console > Monitoring > Alerting**
2. Create alerts for:
   - High error rates (>5% of requests)
   - High latency (>2s p95)
   - Low instance count during peak hours

### View Logs

```bash
# Application logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=swifty-api" --limit=100

# Error logs only
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=swifty-api AND severity>=ERROR" --limit=50
```

### Database Monitoring

```bash
# Check database connections
gcloud sql operations list --instance=swifty-postgres

# View database metrics in Cloud Console
open "https://console.cloud.google.com/sql/instances/swifty-postgres/metrics?project=$PROJECT_ID"
```

---

## Cost Optimization

### Estimated Monthly Costs

| Resource | Configuration | Estimated Cost |
|----------|--------------|----------------|
| Cloud Run | 1M requests/month, 512MB RAM | $5-15 |
| Cloud SQL | db-f1-micro, 10GB storage | $10-15 |
| Egress | ~10GB/month | $1-2 |
| **Total** | | **~$16-32/month** |

### Tips to Reduce Costs

1. **Use appropriate instance sizes**: Start with `db-f1-micro` for Cloud SQL
2. **Set min instances to 0**: Cloud Run scales to zero when idle
3. **Enable Connection Pooling**: Reuse database connections
4. **Optimize image size**: Smaller Docker images = faster cold starts = lower costs
5. **Monitor and set budgets**: Set budget alerts in GCP Console

---

## Troubleshooting

### Issue: "Service Unavailable" or 502 errors

**Solution:**
```bash
# Check logs for errors
gcloud run services logs read swifty-api --region=$REGION --limit=100

# Common causes:
# 1. Database connection issues - verify Cloud SQL instance name
# 2. Missing environment variables - check Cloud Run configuration
# 3. Application crashes - review error logs
```

### Issue: "Database connection timeout"

**Solution:**
```bash
# Verify Cloud SQL instance is running
gcloud sql instances describe swifty-postgres

# Ensure Cloud Run has Cloud SQL instance added
gcloud run services describe swifty-api --region=$REGION

# Check that the connection name is correct:
# Should be: /cloudsql/PROJECT_ID:REGION:swifty-postgres
```

### Issue: CORS errors in React Native app

**Solution:**
```bash
# Update CORS origins
gcloud run services update swifty-api \
  --region=$REGION \
  --set-env-vars "CORS_ORIGINS=https://app-swifty-healthy.apps.tossmini.com,https://app-swifty-healthy.private-apps.tossmini.com"

# Verify configuration
gcloud run services describe swifty-api --region=$REGION --format="yaml(spec.template.spec.containers[0].env)"
```

### Issue: "Permission denied" errors

**Solution:**
```bash
# Grant necessary permissions to Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# For Cloud SQL
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# For Secret Manager
gcloud secrets add-iam-policy-binding swifty-db-password \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Issue: High memory usage or crashes

**Solution:**
```bash
# Increase memory allocation
gcloud run services update swifty-api \
  --region=$REGION \
  --memory 1Gi

# Or increase CPU
gcloud run services update swifty-api \
  --region=$REGION \
  --cpu 2
```

---

## Rolling Back a Deployment

```bash
# List all revisions
gcloud run revisions list --service=swifty-api --region=$REGION

# Route traffic to a previous revision
gcloud run services update-traffic swifty-api \
  --region=$REGION \
  --to-revisions=swifty-api-00001=100
```

---

## Production Checklist

Before going live, ensure:

- [x] Database schema is initialized
- [x] Secrets are stored in Secret Manager (not in code!)
- [x] CORS origins are properly configured
- [x] Custom domain is mapped (if applicable)
- [x] Monitoring and alerts are set up
- [x] Backup strategy is in place
- [x] Resource limits are appropriate for expected traffic
- [x] Health checks are configured
- [x] SSL/TLS certificates are valid
- [x] Budget alerts are configured

---

## Next Steps

1. **Set up automated backups** for Cloud SQL
2. **Configure Cloud Armor** for DDoS protection (if needed)
3. **Implement rate limiting** in the API
4. **Set up Cloud CDN** for static assets (if applicable)
5. **Review security best practices**: [Cloud Run Security Guide](https://cloud.google.com/run/docs/securing/securing-services)

---

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review Cloud Run logs: `gcloud run services logs read swifty-api`
3. Check Cloud SQL status: `gcloud sql instances describe swifty-postgres`
4. Contact GCP Support if needed

---

**Happy Deploying! 🚀**

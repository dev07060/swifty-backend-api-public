#!/bin/bash
# Deploy FastAPI backend to Cloud Run
# Make sure you're logged in: gcloud auth login

set -e

echo "🚀 Deploying Swifty Backend API to Cloud Run"
echo "=============================================="

# Configuration
PROJECT_ID="app-swifty-healthy"  # TODO: Update with your GCP project ID
SERVICE_NAME="swifty-backend-api"
REGION="asia-northeast3"  # Seoul region
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo "📝 Setting GCP project: ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com

# Build the Docker image
echo "🐳 Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

 gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --env-vars-file .env.yaml \
  --add-cloudsql-instances app-swifty-healthy:asia-northeast3:psql-swifty-free \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --port 8080

# Get the service URL
echo ""
echo "✅ Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📝 Next steps:"
echo "   1. Update your mobile app's .env with API_BASE_URL=${SERVICE_URL}"
echo "   2. Test the API: curl ${SERVICE_URL}/docs"
echo ""

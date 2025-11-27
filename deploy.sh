#!/bin/bash
# Deployment script for Swifty Backend API to Google Cloud Platform
# Usage: ./deploy.sh [environment]
# Environments: dev, staging, production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install it: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install it: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    log_info "✓ All prerequisites met"
}

# Get environment configuration
get_environment() {
    ENVIRONMENT=${1:-production}
    
    case $ENVIRONMENT in
        dev|development)
            ENV="development"
            SERVICE_NAME="swifty-api-dev"
            MIN_INSTANCES=0
            MAX_INSTANCES=3
            ;;
        staging|stg)
            ENV="staging"
            SERVICE_NAME="swifty-api-staging"
            MIN_INSTANCES=0
            MAX_INSTANCES=5
            ;;
        prod|production)
            ENV="production"
            SERVICE_NAME="swifty-api"
            MIN_INSTANCES=1
            MAX_INSTANCES=10
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            echo "Usage: $0 [dev|staging|production]"
            exit 1
            ;;
    esac
    
    log_info "Deploying to: ${ENV}"
}

# Load configuration
load_config() {
    log_info "Loading configuration..."
    
    # Prompt for required values if not set
    if [ -z "$PROJECT_ID" ]; then
        read -p "Enter GCP Project ID: " PROJECT_ID
    fi
    
    if [ -z "$REGION" ]; then
        REGION="us-central1"
        log_info "Using default region: $REGION"
    fi
    
    if [ -z "$CLOUDSQL_INSTANCE" ]; then
        read -p "Enter Cloud SQL instance name (e.g., swifty-postgres): " CLOUDSQL_INSTANCE
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    log_info "Configuration loaded"
    log_info "  Project: $PROJECT_ID"
    log_info "  Region: $REGION"
    log_info "  Service: $SERVICE_NAME"
    log_info "  Cloud SQL: $CLOUDSQL_INSTANCE"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    IMAGE_TAG="gcr.io/$PROJECT_ID/$SERVICE_NAME:$(date +%Y%m%d-%H%M%S)"
    IMAGE_LATEST="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
    
    docker build -t $IMAGE_TAG -t $IMAGE_LATEST .
    
    if [ $? -eq 0 ]; then
        log_info "✓ Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi
}

# Push image to Container Registry
push_image() {
    log_info "Pushing image to Container Registry..."
    
    docker push $IMAGE_TAG
    docker push $IMAGE_LATEST
    
    if [ $? -eq 0 ]; then
        log_info "✓ Image pushed successfully"
    else
        log_error "Image push failed"
        exit 1
    fi
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    log_info "Deploying to Cloud Run..."
    
    # Construct environment variables
    ENV_VARS="ENVIRONMENT=$ENV,DB_HOST=/cloudsql/$PROJECT_ID:$REGION:$CLOUDSQL_INSTANCE,DB_PORT=5432,DB_NAME=swifty,DB_USER=swifty_user,GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent,GEMINI_TIMEOUT=30,MAX_IMAGE_SIZE_MB=10,LOG_LEVEL=INFO,CORS_ORIGINS=https://app-swifty-healthy.apps.tossmini.com,https://app-swifty-healthy.private-apps.tossmini.com"
    
    gcloud run deploy $SERVICE_NAME \
        --image $IMAGE_TAG \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated \
        --add-cloudsql-instances $PROJECT_ID:$REGION:$CLOUDSQL_INSTANCE \
        --set-env-vars "$ENV_VARS" \
        --set-secrets "DB_PASSWORD=swifty-db-password:latest,GEMINI_API_KEY=swifty-gemini-api-key:latest" \
        --memory 512Mi \
        --cpu 1 \
        --timeout 300 \
        --max-instances $MAX_INSTANCES \
        --min-instances $MIN_INSTANCES \
        --concurrency 80
    
    if [ $? -eq 0 ]; then
        log_info "✓ Deployment successful"
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Get service URL
get_service_url() {
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    log_info "========================================="
    log_info "Deployment Complete! 🚀"
    log_info "========================================="
    log_info "Service URL: $SERVICE_URL"
    log_info "Environment: $ENV"
    log_info "Region: $REGION"
    log_info "========================================="
    log_info ""
    log_info "Test your API:"
    log_info "  curl $SERVICE_URL/docs"
    log_info ""
    log_info "View logs:"
    log_info "  gcloud run services logs read $SERVICE_NAME --region=$REGION"
}

# Main execution
main() {
    echo "========================================="
    echo "Swifty Backend API - GCP Deployment"
    echo "========================================="
    echo ""
    
    check_prerequisites
    get_environment $1
    load_config
    
    # Confirmation prompt for production
    if [ "$ENV" == "production" ]; then
        log_warn "You are about to deploy to PRODUCTION!"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    build_image
    push_image
    deploy_to_cloud_run
    get_service_url
}

# Run main function with all arguments
main "$@"

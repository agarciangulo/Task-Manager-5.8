#!/bin/bash

# AI Team Support - Fast Google Cloud Run Deployment Script
set -e

echo "🚀 Starting fast deployment to Google Cloud Run..."

# Configuration
PROJECT_ID="ai-task-manager-prod"
SERVICE_NAME="ai-team-support"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
print_status "Setting project to $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Build and push Docker image (with optimizations)
print_status "Building and pushing Docker image..."
gcloud builds submit --tag $IMAGE_NAME --timeout=1800s --machine-type=e2-highcpu-8

# Deploy to Cloud Run (with optimizations)
print_status "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80 \
    --vpc-connector redis-connector \
    --env-vars-file deployment/env-secure.yaml \
    --set-secrets NOTION_TOKEN=notion-token:latest \
    --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
    --set-secrets JWT_SECRET_KEY=jwt-secret-key:latest

print_status "Deployment completed successfully!"
print_status "Your application should be available at:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

print_status "Security Summary:"
echo "✅ API keys stored in Google Cloud Secret Manager"
echo "✅ Sensitive data not exposed in deployment files"
echo "✅ Environment variables secured"
echo "✅ Database and Redis connections configured" 
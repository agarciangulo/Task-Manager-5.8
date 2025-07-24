#!/bin/bash

# AI Team Support - Simple Google Cloud Run Deployment Script
set -e

echo "🚀 Starting AI Team Support deployment to Google Cloud Run..."

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
    print_error "Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
print_status "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs if not already enabled
print_status "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com

# Build and push the Docker image
print_status "Building and pushing Docker image..."
gcloud builds submit --tag $IMAGE_NAME .

# Deploy to Cloud Run
print_status "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 80 \
    --max-instances 10 \
    --set-env-vars-from-file .env.production \
    --add-cloudsql-instances $PROJECT_ID:us-central1:ai-task-manager

print_status "Deployment completed successfully!"
print_status "Your application should be available at:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

echo ""
print_status "Next steps:"
echo "1. Test your application at the URL above"
echo "2. Check logs if there are any issues: gcloud logs tail --service=$SERVICE_NAME"
echo "3. Set up VPC connector for Redis access if needed"
echo "4. Configure monitoring and logging" 
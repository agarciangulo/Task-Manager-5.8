#!/bin/bash

# Gmail Processor - Google Cloud Run Deployment Script
set -e

echo "🚀 Starting Gmail Processor deployment to Google Cloud Run..."

# Configuration
PROJECT_ID="ai-task-manager-prod"
SERVICE_NAME="gmail-processor"
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
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable pubsub.googleapis.com

# Build and push the Docker image
print_status "Building and pushing Docker image for Gmail processor..."
gcloud builds submit --config deployment/cloudbuild-gmail-processor.yaml .

# Deploy to Cloud Run
print_status "Deploying Gmail processor to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 1 \
    --env-vars-file deployment/env-gmail-processor.yaml \
    --add-cloudsql-instances $PROJECT_ID:us-central1:ai-task-manager \
    --vpc-connector redis-connector \
    --set-secrets "NOTION_TOKEN=notion-token:latest,GEMINI_API_KEY=gemini-api-key:latest,JWT_SECRET_KEY=jwt-secret-key:latest,GMAIL_ADDRESS=gmail-address:latest,GMAIL_APP_PASSWORD=gmail-app-password:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

print_status "Gmail processor deployed at: $SERVICE_URL"

# Create Pub/Sub topic for scheduler
print_status "Creating Pub/Sub topic..."
gcloud pubsub topics create gmail-processor-trigger --quiet || echo "Topic already exists"

# Create Cloud Scheduler job
print_status "Creating Cloud Scheduler job..."
gcloud scheduler jobs create http gmail-processor-scheduler \
    --schedule="*/5 * * * *" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --attempt-deadline=300s \
    --time-zone="UTC" \
    --description="Trigger Gmail processing every 5 minutes" \
    --quiet || echo "Scheduler job already exists"

print_status "Deployment completed successfully!"
print_status "Gmail processor will run every 5 minutes automatically"

echo ""
print_status "Service Details:"
echo "   Service URL: $SERVICE_URL"
echo "   Schedule: Every 5 minutes"
echo "   Region: $REGION"
echo ""
print_status "Monitor your service:"
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "   gcloud scheduler jobs describe gmail-processor-scheduler"
echo ""
print_status "View logs:"
echo "   gcloud logs tail --service=$SERVICE_NAME"

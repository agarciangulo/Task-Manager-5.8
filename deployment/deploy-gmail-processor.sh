#!/bin/bash

# Deploy Gmail Processor to Google Cloud Run with Cloud Scheduler
# This creates a truly continuous Gmail processing system

set -e

# Configuration
PROJECT_ID="your-project-id"  # Replace with your actual project ID
REGION="us-central1"
SERVICE_NAME="gmail-processor"
SCHEDULER_NAME="gmail-processor-scheduler"
TOPIC_NAME="gmail-processor-trigger"

echo "🚀 Deploying Gmail Processor to Google Cloud Run..."

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable pubsub.googleapis.com

# Build and deploy to Cloud Run
echo "🏗️ Building and deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 1 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Service deployed at: $SERVICE_URL"

# Create Pub/Sub topic for scheduler
echo "📢 Creating Pub/Sub topic..."
gcloud pubsub topics create $TOPIC_NAME --quiet || echo "Topic already exists"

# Create Cloud Scheduler job
echo "⏰ Creating Cloud Scheduler job..."
gcloud scheduler jobs create http $SCHEDULER_NAME \
    --schedule="*/5 * * * *" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --attempt-deadline=300s \
    --time-zone="UTC" \
    --description="Trigger Gmail processing every 5 minutes" \
    --quiet || echo "Scheduler job already exists"

echo "✅ Deployment complete!"
echo ""
echo "📊 Service Details:"
echo "   Service URL: $SERVICE_URL"
echo "   Schedule: Every 5 minutes"
echo "   Region: $REGION"
echo ""
echo "🔍 Monitor your service:"
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "   gcloud scheduler jobs describe $SCHEDULER_NAME"
echo ""
echo "📝 View logs:"
echo "   gcloud logs tail --service=$SERVICE_NAME" 
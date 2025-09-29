#!/bin/bash

# Deploy Gmail Processor to Google Cloud Run with Cloud Scheduler
# This creates a truly continuous Gmail processing system

set -e

# Configuration
PROJECT_ID="ai-task-manager-prod"  # Replace with your actual project ID
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
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,DATABASE_URL=postgresql://postgres:S2uwupRe@34.58.40.214:5432/email_archive,REDIS_URL=redis://10.96.205.195:6379/0,NOTION_DATABASE_ID=1e35c6ec3b80804f922ce6cc63d0c36b,NOTION_FEEDBACK_DB_ID=1cc5c6ec3b8080ab934feb388e729447,NOTION_PARENT_PAGE_ID=2175c6ec3b8080d183d0c0e4fb219f9d,NOTION_USERS_DB_ID=2175c6ec3b8080ac9d60c035a3000f52" \
    --add-cloudsql-instances ai-task-manager-prod:us-central1:ai-task-manager \
    --vpc-connector redis-connector \
    --set-secrets "NOTION_TOKEN=notion-token:latest,GEMINI_API_KEY=gemini-api-key:latest,JWT_SECRET_KEY=jwt-secret-key:latest"

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
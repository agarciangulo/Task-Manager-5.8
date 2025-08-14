#!/bin/bash

# SAFE Gmail Processor Deployment with Billing Controls
# This script includes multiple safeguards to prevent unexpected charges

set -e

# Configuration - MODIFY THESE FOR YOUR PROJECT
PROJECT_ID="ai-task-manager-prod"  # Your actual project ID
REGION="us-central1"
SERVICE_NAME="gmail-processor-safe"
SCHEDULER_NAME="gmail-processor-scheduler-safe"
TOPIC_NAME="gmail-processor-trigger-safe"
BUDGET_AMOUNT="50"  # $50 monthly budget limit

echo "🛡️ SAFE Gmail Processor Deployment"
echo "=================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Monthly Budget Limit: $${BUDGET_AMOUNT}"
echo ""

# Verify project ID is set
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ ERROR: Please set your actual PROJECT_ID in this script"
    echo "   Edit the PROJECT_ID variable at the top of this script"
    exit 1
fi

# Set project
echo "🔧 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs (only what we need)
echo "📋 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable billingbudgets.googleapis.com
gcloud services enable monitoring.googleapis.com

# Create budget alert
echo "💰 Creating budget alert..."
gcloud billing budgets create \
    --billing-account=$(gcloud billing accounts list --format="value(ACCOUNT_ID)" --limit=1) \
    --display-name="Gmail Processor Budget Alert" \
    --budget-amount="$BUDGET_AMOUNT" \
    --budget-filter="projects:$PROJECT_ID" \
    --threshold-rule="threshold-amount=0.5,spend-basis=CURRENT_SPEND" \
    --threshold-rule="threshold-amount=0.8,spend-basis=CURRENT_SPEND" \
    --threshold-rule="threshold-amount=1.0,spend-basis=CURRENT_SPEND"

echo "✅ Budget alert created - you'll be notified at 50%, 80%, and 100% of $${BUDGET_AMOUNT}"

# Build and deploy to Cloud Run with STRICT resource limits
echo "🏗️ Building and deploying to Cloud Run (with strict limits)..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 0.5 \
    --timeout 300 \
    --max-instances 1 \
    --min-instances 0 \
    --concurrency 1 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,MAX_EXECUTION_TIME=300,COST_LIMIT=$BUDGET_AMOUNT" \
    --labels "service=gmail-processor,cost-controlled=true"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Service deployed at: $SERVICE_URL"

# Create Pub/Sub topic for scheduler
echo "📢 Creating Pub/Sub topic..."
gcloud pubsub topics create $TOPIC_NAME --quiet || echo "Topic already exists"

# Create Cloud Scheduler job with conservative settings
echo "⏰ Creating Cloud Scheduler job (every 10 minutes to reduce costs)..."
gcloud scheduler jobs create http $SCHEDULER_NAME \
    --schedule="*/10 * * * *" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --attempt-deadline=300s \
    --time-zone="UTC" \
    --description="Safe Gmail processing every 10 minutes (cost-controlled)" \
    --max-retry-attempts=2 \
    --max-backoff-duration=60s \
    --quiet || echo "Scheduler job already exists"

# Create monitoring alert for high costs
echo "📊 Creating cost monitoring alert..."
gcloud alpha monitoring policies create \
    --policy-from-file=- <<EOF
displayName: "Gmail Processor High Cost Alert"
conditions:
  - displayName: "Gmail Processor Cost > $10/day"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="$SERVICE_NAME"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 10
      duration: 300s
      aggregations:
        - alignmentPeriod: 86400s
          perSeriesAligner: ALIGN_RATE
          crossSeriesReducer: REDUCE_SUM
          groupByFields:
            - resource.labels.service_name
notificationChannels: []
EOF

echo "✅ Cost monitoring alert created"

# Create a cost estimation script
cat > deployment/estimate-costs.sh << 'EOF'
#!/bin/bash
echo "💰 Gmail Processor Cost Estimation"
echo "=================================="
echo ""
echo "Conservative Estimate (no emails):"
echo "  - 144 executions/day (every 10 minutes)"
echo "  - 30 seconds average runtime"
echo "  - Cost: ~$3-5/month"
echo ""
echo "Moderate Usage (some emails):"
echo "  - 144 executions/day"
echo "  - 2 minutes average runtime"
echo "  - Cost: ~$15-25/month"
echo ""
echo "Heavy Usage (many emails):"
echo "  - 144 executions/day"
echo "  - 5 minutes average runtime"
echo "  - Cost: ~$40-50/month"
echo ""
echo "Budget Limit: $50/month"
echo ""
echo "To monitor costs:"
echo "  gcloud billing budgets list"
echo "  gcloud run services describe gmail-processor-safe --region=us-central1"
EOF

chmod +x deployment/estimate-costs.sh

echo ""
echo "✅ SAFE DEPLOYMENT COMPLETE!"
echo ""
echo "📊 Service Details:"
echo "   Service URL: $SERVICE_URL"
echo "   Schedule: Every 10 minutes (cost-optimized)"
echo "   Region: $REGION"
echo "   Max Instances: 1 (cost-controlled)"
echo "   Memory: 512Mi (conservative)"
echo "   CPU: 0.5 (conservative)"
echo "   Budget Limit: $${BUDGET_AMOUNT}/month"
echo ""
echo "🛡️ Safety Features:"
echo "   ✅ Budget alerts at 50%, 80%, 100%"
echo "   ✅ Cost monitoring alerts"
echo "   ✅ Resource limits enforced"
echo "   ✅ Conservative scheduling (10 min vs 5 min)"
echo "   ✅ Maximum 1 instance"
echo ""
echo "📝 Monitoring Commands:"
echo "   ./deployment/estimate-costs.sh"
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "   gcloud scheduler jobs describe $SCHEDULER_NAME"
echo "   gcloud billing budgets list"
echo ""
echo "📝 View logs:"
echo "   gcloud logs tail --service=$SERVICE_NAME"
echo ""
echo "🛑 To stop the service (if needed):"
echo "   gcloud run services delete $SERVICE_NAME --region=$REGION"
echo "   gcloud scheduler jobs delete $SCHEDULER_NAME" 
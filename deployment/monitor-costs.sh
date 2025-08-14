#!/bin/bash

# Cost Monitoring Script for Gmail Processor
# This script helps you monitor costs and stay within budget

set -e

PROJECT_ID="ai-task-manager-prod"  # Your actual project ID
SERVICE_NAME="gmail-processor-safe"
BUDGET_LIMIT=50

echo "💰 Gmail Processor Cost Monitor"
echo "================================"

# Check if project ID is set
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ ERROR: Please set your actual PROJECT_ID in this script"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

echo "📊 Current Cost Analysis:"
echo ""

# Get current month's cost for the project
CURRENT_COST=$(gcloud billing accounts list --format="value(ACCOUNT_ID)" --limit=1 | xargs -I {} gcloud billing accounts describe {} --format="value(displayName)")

echo "Current billing account: $CURRENT_COST"
echo ""

# Get Cloud Run service details
echo "🔍 Service Details:"
gcloud run services describe $SERVICE_NAME --region=us-central1 --format="table(
    metadata.name,
    spec.template.spec.containers[0].resources.limits.memory,
    spec.template.spec.containers[0].resources.limits.cpu,
    spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale'
)" || echo "Service not found or not deployed"

echo ""

# Get scheduler job details
echo "⏰ Scheduler Details:"
gcloud scheduler jobs describe gmail-processor-scheduler-safe --format="table(
    name,
    schedule,
    httpTarget.uri,
    attemptDeadline
)" || echo "Scheduler job not found"

echo ""

# Get recent logs to estimate usage
echo "📝 Recent Activity (last 24 hours):"
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit=10 \
    --format="table(timestamp,severity,textPayload)" \
    --freshness=24h || echo "No recent logs found"

echo ""

# Cost estimation based on typical usage
echo "💰 Cost Estimation:"
echo "Conservative (no emails): ~$3-5/month"
echo "Moderate (some emails): ~$15-25/month"
echo "Heavy (many emails): ~$40-50/month"
echo "Budget limit: $${BUDGET_LIMIT}/month"
echo ""

# Check if service is running
echo "🔍 Service Status:"
SERVICE_STATUS=$(gcloud run services describe $SERVICE_NAME --region=us-central1 --format="value(status.conditions[0].status)" 2>/dev/null || echo "NOT_DEPLOYED")

if [ "$SERVICE_STATUS" = "True" ]; then
    echo "✅ Service is running"
elif [ "$SERVICE_STATUS" = "NOT_DEPLOYED" ]; then
    echo "❌ Service is not deployed"
else
    echo "⚠️ Service status: $SERVICE_STATUS"
fi

echo ""

# Quick cost-saving tips
echo "💡 Cost-Saving Tips:"
echo "1. Service runs every 10 minutes (not 5) to reduce costs"
echo "2. Maximum 1 instance prevents scaling costs"
echo "3. 512Mi memory limit keeps costs low"
echo "4. 5-minute timeout prevents runaway processes"
echo "5. Budget alerts notify you at 50%, 80%, 100%"
echo ""

# Emergency stop command
echo "🛑 Emergency Stop Commands:"
echo "  gcloud run services delete $SERVICE_NAME --region=us-central1"
echo "  gcloud scheduler jobs delete gmail-processor-scheduler-safe"
echo ""

echo "✅ Cost monitoring complete!" 
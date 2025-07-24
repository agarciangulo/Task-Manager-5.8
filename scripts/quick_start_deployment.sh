#!/bin/bash

# Quick Start Deployment Script for Google Cloud
# This script helps you get started with the deployment process

set -e  # Exit on any error

echo "🚀 AI Team Support - Google Cloud Quick Start"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud CLI (gcloud) is not installed."
        echo "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed."
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning "No .env file found. Creating from template..."
        if [ -f "env.production.template" ]; then
            cp env.production.template .env
            print_warning "Please edit .env file with your actual values before proceeding."
            echo "Press Enter when you're ready to continue..."
            read
        else
            print_error "No environment template found. Please create a .env file manually."
            exit 1
        fi
    fi
    
    print_success "Prerequisites check completed!"
}

# Get project configuration
get_project_config() {
    print_status "Getting project configuration..."
    
    # Get current project
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_PROJECT" ]; then
        print_warning "No Google Cloud project is set."
        echo "Please enter your Google Cloud project ID:"
        read -p "Project ID: " PROJECT_ID
        
        gcloud config set project "$PROJECT_ID"
        print_success "Project set to: $PROJECT_ID"
    else
        print_success "Using project: $CURRENT_PROJECT"
        PROJECT_ID="$CURRENT_PROJECT"
    fi
    
    # Get region
    echo "Please select a region for deployment:"
    echo "1) us-central1 (Iowa) - Recommended"
    echo "2) us-east1 (South Carolina)"
    echo "3) europe-west1 (Belgium)"
    echo "4) asia-northeast1 (Tokyo)"
    read -p "Enter choice (1-4): " REGION_CHOICE
    
    case $REGION_CHOICE in
        1) REGION="us-central1" ;;
        2) REGION="us-east1" ;;
        3) REGION="europe-west1" ;;
        4) REGION="asia-northeast1" ;;
        *) REGION="us-central1" ;;
    esac
    
    print_success "Selected region: $REGION"
}

# Enable required APIs
enable_apis() {
    print_status "Enabling required Google Cloud APIs..."
    
    APIs=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "sqladmin.googleapis.com"
        "redis.googleapis.com"
        "secretmanager.googleapis.com"
        "storage.googleapis.com"
        "compute.googleapis.com"
    )
    
    for api in "${APIs[@]}"; do
        print_status "Enabling $api..."
        gcloud services enable "$api" --quiet
    done
    
    print_success "All required APIs enabled!"
}

# Create database
create_database() {
    print_status "Setting up Cloud SQL PostgreSQL instance..."
    
    # Generate a strong password
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # Create PostgreSQL instance
    gcloud sql instances create ai-team-support-db \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --storage-type=SSD \
        --storage-size=10GB \
        --backup-start-time=02:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=03:00 \
        --quiet
    
    # Create database
    gcloud sql databases create email_archive --instance=ai-team-support-db --quiet
    
    # Create user
    gcloud sql users create ai_app_user \
        --instance=ai-team-support-db \
        --password="$DB_PASSWORD" \
        --quiet
    
    # Get database IP
    DB_IP=$(gcloud sql instances describe ai-team-support-db --format="value(ipAddresses[0].ipAddress)")
    
    print_success "Database created successfully!"
    print_status "Database IP: $DB_IP"
    print_status "Database Password: $DB_PASSWORD"
    print_warning "Please save the database password for later use!"
    
    # Store password in environment variable for later use
    export DB_PASSWORD
    export DB_IP
}

# Create Redis instance
create_redis() {
    print_status "Setting up Cloud Memorystore Redis instance..."
    
    gcloud redis instances create ai-team-support-redis \
        --size=1 \
        --region="$REGION" \
        --redis-version=redis_7_0 \
        --quiet
    
    # Get Redis IP
    REDIS_IP=$(gcloud redis instances describe ai-team-support-redis --region="$REGION" --format="value(host)")
    
    print_success "Redis instance created successfully!"
    print_status "Redis IP: $REDIS_IP"
    
    export REDIS_IP
}

# Build and deploy application
build_and_deploy() {
    print_status "Building and deploying application..."
    
    # Build Docker image
    print_status "Building Docker image..."
    gcloud builds submit --tag "gcr.io/$PROJECT_ID/ai-team-support" --quiet
    
    # Deploy to Cloud Run
    print_status "Deploying to Cloud Run..."
    gcloud run deploy ai-team-support \
        --image "gcr.io/$PROJECT_ID/ai-team-support" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --port 5000 \
        --memory 2Gi \
        --cpu 2 \
        --max-instances 10 \
        --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=0" \
        --quiet
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe ai-team-support --region="$REGION" --format="value(status.url)")
    
    print_success "Application deployed successfully!"
    print_status "Service URL: $SERVICE_URL"
    
    export SERVICE_URL
}

# Test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Wait a moment for the service to be ready
    sleep 10
    
    # Test the service
    if curl -s "$SERVICE_URL/" > /dev/null; then
        print_success "Application is responding!"
    else
        print_warning "Application might still be starting up. Please check manually."
    fi
}

# Generate deployment summary
generate_summary() {
    print_status "Generating deployment summary..."
    
    cat > deployment_summary.txt << EOF
AI Team Support - Google Cloud Deployment Summary
================================================

Project ID: $PROJECT_ID
Region: $REGION
Service URL: $SERVICE_URL

Database Configuration:
- Instance: ai-team-support-db
- IP: $DB_IP
- Password: $DB_PASSWORD
- Connection String: postgresql://ai_app_user:$DB_PASSWORD@$DB_IP:5432/email_archive

Redis Configuration:
- Instance: ai-team-support-redis
- IP: $REDIS_IP
- Connection String: redis://$REDIS_IP:6379/0

Next Steps:
1. Update your .env file with the database and Redis connection strings
2. Store sensitive data in Google Cloud Secret Manager
3. Deploy background services (Celery workers)
4. Set up monitoring and logging
5. Configure custom domain (optional)

For detailed instructions, see: docs/GOOGLE_CLOUD_DEPLOYMENT.md
EOF
    
    print_success "Deployment summary saved to: deployment_summary.txt"
}

# Main execution
main() {
    echo "This script will help you deploy your AI Team Support application to Google Cloud."
    echo "It will create the necessary infrastructure and deploy your application."
    echo ""
    echo "Press Enter to continue or Ctrl+C to cancel..."
    read
    
    check_prerequisites
    get_project_config
    enable_apis
    create_database
    create_redis
    build_and_deploy
    test_deployment
    generate_summary
    
    echo ""
    print_success "Quick start deployment completed!"
    echo ""
    echo "Your application is now running at: $SERVICE_URL"
    echo ""
    echo "Next steps:"
    echo "1. Review deployment_summary.txt for connection details"
    echo "2. Update your .env file with the database and Redis connection strings"
    echo "3. Follow the detailed deployment guide for background services"
    echo "4. Set up monitoring and logging"
    echo ""
    echo "For detailed instructions, see: docs/GOOGLE_CLOUD_DEPLOYMENT.md"
}

# Run main function
main "$@" 
# 🚀 Google Cloud Deployment Guide

This guide will walk you through deploying your AI Team Support application to Google Cloud step by step.

## 📋 **Prerequisites**

Before starting, ensure you have:

- [ ] Google Cloud account with billing enabled
- [ ] Google Cloud CLI (gcloud) installed and configured
- [ ] Docker installed locally
- [ ] All required API keys and credentials ready
- [ ] Domain name (optional, for custom domain)

## 🎯 **Deployment Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloud Run     │    │   Cloud SQL     │    │  Memorystore    │
│   (Flask App)   │◄──►│  (PostgreSQL)   │    │    (Redis)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Cloud Storage  │
                    │ (ChromaDB Data) │
                    └─────────────────┘
```

## 📝 **Step 1: Project Setup**

### 1.1 Create Google Cloud Project

```bash
# Create new project
gcloud projects create ai-team-support-[YOUR-NAME] --name="AI Team Support"

# Set the project as default
gcloud config set project ai-team-support-[YOUR-NAME]

# Enable billing (replace with your billing account)
gcloud billing projects link ai-team-support-[YOUR-NAME] --billing-account=[BILLING-ACCOUNT-ID]
```

### 1.2 Enable Required APIs

```bash
# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  compute.googleapis.com
```

## 🗄️ **Step 2: Database Setup (Cloud SQL)**

### 2.1 Create PostgreSQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create ai-team-support-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=02:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=03:00

# Create database
gcloud sql databases create email_archive --instance=ai-team-support-db

# Create user
gcloud sql users create ai_app_user \
  --instance=ai-team-support-db \
  --password=[STRONG_PASSWORD]
```

### 2.2 Get Database Connection Info

```bash
# Get connection info
gcloud sql instances describe ai-team-support-db --format="value(connectionName)"

# Note the connection name for later use
# Format: PROJECT_ID:REGION:INSTANCE_NAME
```

## 🔴 **Step 3: Redis Setup (Memorystore)**

### 3.1 Create Redis Instance

```bash
# Create Redis instance
gcloud redis instances create ai-team-support-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

### 3.2 Get Redis Connection Info

```bash
# Get Redis IP
gcloud redis instances describe ai-team-support-redis \
  --region=us-central1 \
  --format="value(host)"
```

## 🔐 **Step 4: Secrets Management**

### 4.1 Store Sensitive Data in Secret Manager

```bash
# Store API keys and secrets
echo -n "your_notion_token_here" | gcloud secrets create notion-token --data-file=-
echo -n "your_gemini_api_key_here" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your_jwt_secret_key_here" | gcloud secrets create jwt-secret-key --data-file=-
echo -n "your_notion_database_id_here" | gcloud secrets create notion-database-id --data-file=-
echo -n "your_notion_feedback_db_id_here" | gcloud secrets create notion-feedback-db-id --data-file=-
echo -n "your_notion_users_db_id_here" | gcloud secrets create notion-users-db-id --data-file=-
echo -n "your_notion_parent_page_id_here" | gcloud secrets create notion-parent-page-id --data-file=-
```

## 🏗️ **Step 5: Build and Deploy Application**

### 5.1 Build Docker Image

```bash
# Build the image
gcloud builds submit --tag gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support

# Or build locally and push
docker build -t gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support .
docker push gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support
```

### 5.2 Deploy to Cloud Run

```bash
# Deploy the main application
gcloud run deploy ai-team-support \
  --image gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 5000 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=0" \
  --set-secrets="NOTION_TOKEN=notion-token:latest" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --set-secrets="JWT_SECRET_KEY=jwt-secret-key:latest" \
  --set-secrets="NOTION_DATABASE_ID=notion-database-id:latest" \
  --set-secrets="NOTION_FEEDBACK_DB_ID=notion-feedback-db-id:latest" \
  --set-secrets="NOTION_USERS_DB_ID=notion-users-db-id:latest" \
  --set-secrets="NOTION_PARENT_PAGE_ID=notion-parent-page-id:latest"
```

### 5.3 Set Environment Variables

```bash
# Set additional environment variables
gcloud run services update ai-team-support \
  --region us-central1 \
  --update-env-vars="DATABASE_URL=postgresql://ai_app_user:[PASSWORD]@[DB_IP]:5432/email_archive" \
  --update-env-vars="REDIS_URL=redis://[REDIS_IP]:6379/0" \
  --update-env-vars="AI_PROVIDER=gemini" \
  --update-env-vars="CHAT_MODEL=gemini-1.5-flash" \
  --update-env-vars="SIMILARITY_MODE=hybrid" \
  --update-env-vars="SIMILARITY_THRESHOLD=0.7" \
  --update-env-vars="ENABLE_AUTHENTICATION=True" \
  --update-env-vars="EMAIL_ARCHIVE_ENABLED=True" \
  --update-env-vars="ACTIVITY_RECOGNITION_ENABLED=True"
```

## 🔄 **Step 6: Deploy Background Services**

### 6.1 Deploy Celery Worker

```bash
# Deploy Celery worker
gcloud run deploy ai-team-support-worker \
  --image gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --port 5000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5 \
  --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=0" \
  --set-secrets="NOTION_TOKEN=notion-token:latest" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --set-secrets="JWT_SECRET_KEY=jwt-secret-key:latest" \
  --set-secrets="NOTION_DATABASE_ID=notion-database-id:latest" \
  --set-secrets="NOTION_FEEDBACK_DB_ID=notion-feedback-db-id:latest" \
  --set-secrets="NOTION_USERS_DB_ID=notion-users-db-id:latest" \
  --set-secrets="NOTION_PARENT_PAGE_ID=notion-parent-page-id:latest" \
  --command="celery" \
  --args="-A,src.core.services.celery_config,worker,--loglevel=info,--concurrency=2"
```

### 6.2 Deploy Celery Beat (Scheduler)

```bash
# Deploy Celery beat
gcloud run deploy ai-team-support-beat \
  --image gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --port 5000 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 1 \
  --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=0" \
  --set-secrets="NOTION_TOKEN=notion-token:latest" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --set-secrets="JWT_SECRET_KEY=jwt-secret-key:latest" \
  --set-secrets="NOTION_DATABASE_ID=notion-database-id:latest" \
  --set-secrets="NOTION_FEEDBACK_DB_ID=notion-feedback-db-id:latest" \
  --set-secrets="NOTION_USERS_DB_ID=notion-users-db-id:latest" \
  --set-secrets="NOTION_PARENT_PAGE_ID=notion-parent-page-id:latest" \
  --command="celery" \
  --args="-A,src.core.services.celery_config,beat,--loglevel=info"
```

## 🗄️ **Step 7: Database Initialization**

### 7.1 Run Database Setup Script

```bash
# Create a temporary Cloud Run job to initialize the database
gcloud run jobs create db-setup \
  --image gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support \
  --region us-central1 \
  --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=0" \
  --set-secrets="NOTION_TOKEN=notion-token:latest" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --set-secrets="JWT_SECRET_KEY=jwt-secret-key:latest" \
  --set-secrets="NOTION_DATABASE_ID=notion-database-id:latest" \
  --set-secrets="NOTION_FEEDBACK_DB_ID=notion-feedback-db-id:latest" \
  --set-secrets="NOTION_USERS_DB_ID=notion-users-db-id:latest" \
  --set-secrets="NOTION_PARENT_PAGE_ID=notion-parent-page-id:latest" \
  --command="python" \
  --args="scripts/setup_production_db.py"

# Execute the job
gcloud run jobs execute db-setup --region us-central1
```

## 🌐 **Step 8: Domain and SSL Setup**

### 8.1 Map Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service ai-team-support \
  --domain your-domain.com \
  --region us-central1
```

### 8.2 Verify SSL Certificate

```bash
# Check domain mapping status
gcloud run domain-mappings describe \
  --domain your-domain.com \
  --region us-central1
```

## 📊 **Step 9: Monitoring and Logging**

### 9.1 Set Up Cloud Monitoring

```bash
# Create monitoring workspace
gcloud monitoring workspaces create \
  --display-name="AI Team Support Monitoring"
```

### 9.2 Set Up Logging

```bash
# Create log sink
gcloud logging sinks create ai-team-support-logs \
  storage.googleapis.com/[BUCKET_NAME] \
  --log-filter="resource.type=cloud_run_revision"
```

## ✅ **Step 10: Testing and Verification**

### 10.1 Test Application Endpoints

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe ai-team-support \
  --region us-central1 \
  --format="value(status.url)")

# Test health endpoint
curl -X GET "$SERVICE_URL/"

# Test API endpoints
curl -X POST "$SERVICE_URL/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass","full_name":"Test User"}'
```

### 10.2 Verify Database Connection

```bash
# Check database connectivity
gcloud run jobs create db-test \
  --image gcr.io/ai-team-support-[YOUR-NAME]/ai-team-support \
  --region us-central1 \
  --command="python" \
  --args="-c,import psycopg2; conn=psycopg2.connect('$DATABASE_URL'); print('DB OK')"

gcloud run jobs execute db-test --region us-central1
```

## 🔧 **Troubleshooting**

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check Cloud SQL proxy
   gcloud sql instances describe ai-team-support-db
   
   # Test connection
   gcloud sql connect ai-team-support-db --user=ai_app_user
   ```

2. **Redis Connection Failed**
   ```bash
   # Check Redis instance
   gcloud redis instances describe ai-team-support-redis --region=us-central1
   ```

3. **Application Not Starting**
   ```bash
   # Check logs
   gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-team-support" --limit=50
   ```

4. **Environment Variables Not Loading**
   ```bash
   # Check secrets
   gcloud secrets list
   
   # Verify secret values
   gcloud secrets versions access latest --secret=notion-token
   ```

## 💰 **Cost Optimization**

### Resource Sizing

- **Start Small**: Use `db-f1-micro` for database, `512Mi` for workers
- **Scale Up**: Monitor usage and increase resources as needed
- **Auto-scaling**: Cloud Run automatically scales based on demand

### Cost Monitoring

```bash
# Set up billing alerts
gcloud billing budgets create \
  --billing-account=[BILLING-ACCOUNT] \
  --display-name="AI Team Support Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

## 🚀 **Next Steps**

After successful deployment:

1. **Set up monitoring dashboards**
2. **Configure backup strategies**
3. **Implement CI/CD pipeline**
4. **Set up staging environment**
5. **Configure custom domain and SSL**
6. **Set up user management and access controls**

## 📞 **Support**

If you encounter issues:

1. Check the troubleshooting section above
2. Review Cloud Run logs: `gcloud logs read`
3. Check Cloud SQL logs: `gcloud sql logs tail`
4. Verify environment variables and secrets
5. Test database connectivity

---

**🎉 Congratulations! Your AI Team Support application is now deployed on Google Cloud!** 
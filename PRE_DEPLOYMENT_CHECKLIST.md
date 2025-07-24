# 📋 Pre-Deployment Checklist

## 🔑 **API Keys & Credentials**

### **Notion Integration** ✅
- [ ] Create Notion integration at [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
- [ ] Get Internal Integration Token
- [ ] Note down the token for `NOTION_TOKEN`

### **Google AI (Gemini)** ✅
- [ ] Create API key at [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
- [ ] Copy the API key for `GEMINI_API_KEY`

### **JWT Secret Key** ✅
- [ ] Generate secure JWT key: `python scripts/generate_jwt_key.py`
- [ ] Copy the generated key for `JWT_SECRET_KEY`

## 🗄️ **Notion Database Setup**

### **Main Tasks Database** ✅
- [ ] Create new database in Notion
- [ ] Add required properties:
  - Title (default)
  - Status (Select: "Not Started", "In Progress", "Done")
  - Priority (Select: "Low", "Medium", "High")
  - Due Date (Date)
  - Assignee (Person)
  - Project (Text)
  - Tags (Multi-select)
- [ ] Share database with your integration
- [ ] Copy database ID from URL for `NOTION_DATABASE_ID`

### **Users Database** ✅
- [ ] Create new database in Notion
- [ ] Add these exact properties:
  - **UserID** (Title) - Primary identifier
  - **PasswordHash** (Text) - Will be auto-populated
  - **FullName** (Text) - User's full name
  - **Role** (Select) - Options: "user", "admin"
  - **Email** (Email) - User's email address
  - **TaskDatabaseID** (Text) - Will be auto-populated
  - **CreatedAt** (Date) - Auto-populated
  - **UpdatedAt** (Date) - Auto-populated
  - **LastLogin** (Date) - Auto-populated
  - **IsActive** (Checkbox) - Default: true
- [ ] Share database with your integration
- [ ] Copy database ID for `NOTION_USERS_DB_ID`

### **Feedback Database** ✅
- [ ] Create new database in Notion
- [ ] Add properties:
  - Title (default)
  - Feedback (Text)
  - User (Person)
  - Date (Date)
  - Category (Select)
  - Status (Select: "Open", "In Progress", "Resolved")
- [ ] Share database with your integration
- [ ] Copy database ID for `NOTION_FEEDBACK_DB_ID`

### **Parent Page** ✅
- [ ] Create a page in Notion
- [ ] This page will be where user task databases are created
- [ ] Share page with your integration
- [ ] Copy page ID for `NOTION_PARENT_PAGE_ID`

## 🌐 **Google Cloud Setup**

### **Google Cloud Account** ✅
- [ ] Create Google Cloud account
- [ ] Set up billing account
- [ ] Install Google Cloud CLI (`gcloud`)
- [ ] Authenticate: `gcloud auth login`

### **Google Cloud Project** ✅
- [ ] Create new project
- [ ] Enable billing
- [ ] Set as default: `gcloud config set project [PROJECT_ID]`

### **Billing Alerts** ✅
- [ ] Set up billing alerts ($50-100 recommended)
- [ ] Configure email notifications

## 💻 **Local Environment Setup**

### **Environment File** ✅
- [ ] Copy `env.production.template` to `.env`
- [ ] Fill in all required values:
  ```bash
  # API Keys
  NOTION_TOKEN=your_notion_token_here
  GEMINI_API_KEY=your_gemini_api_key_here
  JWT_SECRET_KEY=your_jwt_secret_key_here
  
  # Notion Database IDs
  NOTION_DATABASE_ID=your_main_database_id
  NOTION_FEEDBACK_DB_ID=your_feedback_db_id
  NOTION_USERS_DB_ID=your_users_db_id
  NOTION_PARENT_PAGE_ID=your_parent_page_id
  ```

### **Local Testing** ✅
- [ ] Test locally: `docker-compose up -d`
- [ ] Verify application starts correctly
- [ ] Test basic functionality
- [ ] Check database connections

## 🔧 **Technical Requirements**

### **Docker** ✅
- [ ] Install Docker Desktop
- [ ] Verify installation: `docker --version`

### **Google Cloud CLI** ✅
- [ ] Install gcloud CLI
- [ ] Verify installation: `gcloud --version`
- [ ] Authenticate: `gcloud auth login`

### **Domain Name (Optional)** ✅
- [ ] Purchase domain name (optional)
- [ ] Have DNS access ready

## 📊 **Resource Planning**

### **Expected Costs** ✅
- **Cloud SQL**: ~$25-50/month (db-f1-micro)
- **Cloud Run**: ~$10-30/month (depending on usage)
- **Memorystore**: ~$15-25/month
- **Total**: ~$50-100/month

### **Storage Requirements** ✅
- **Database**: Start with 10GB
- **Application**: 2-4GB
- **ChromaDB**: 1-5GB (depending on embeddings)

## 🚨 **Security Considerations**

### **API Key Security** ✅
- [ ] Never commit API keys to version control
- [ ] Use Google Cloud Secret Manager in production
- [ ] Rotate keys regularly

### **Database Security** ✅
- [ ] Use strong passwords for database users
- [ ] Enable SSL connections
- [ ] Restrict network access

### **Application Security** ✅
- [ ] Use HTTPS in production
- [ ] Enable authentication
- [ ] Set up proper CORS policies

## 📝 **Documentation**

### **Credentials Storage** ✅
- [ ] Store all credentials securely
- [ ] Create a secure password manager entry
- [ ] Document all database IDs and tokens

### **Deployment Notes** ✅
- [ ] Note down your Google Cloud project ID
- [ ] Document your chosen region
- [ ] Keep track of all resource names

## ✅ **Final Verification**

### **Before Deployment** ✅
- [ ] All API keys are working
- [ ] Notion databases are accessible
- [ ] Local testing passes
- [ ] Environment variables are set
- [ ] Google Cloud project is ready
- [ ] Billing is configured

---

## 🚀 **Ready to Deploy!**

Once you've completed all items above, you're ready to deploy using:

```bash
# Option 1: Quick Start (Recommended)
./scripts/quick_start_deployment.sh

# Option 2: Manual Deployment
# Follow docs/GOOGLE_CLOUD_DEPLOYMENT.md
```

## 📞 **Need Help?**

If you get stuck on any of these steps:

1. **Notion Setup**: Check Notion's integration documentation
2. **Google Cloud**: Use `gcloud help` or Google Cloud documentation
3. **Local Testing**: Check Docker logs with `docker-compose logs`
4. **General Issues**: Review the troubleshooting section in the deployment guide

---

**🎯 Remember**: Take your time with this setup. It's better to get everything right before deployment than to fix issues in production! 
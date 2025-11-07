# AI Team Support

An AI-powered task management system that automatically extracts tasks from emails, processes them with AI insights, and syncs them to Notion databases. Built with Flask, PostgreSQL, Redis, and Google Cloud.

## 🎯 What This Project Does

**AI Team Support** helps teams manage tasks by:

- 📧 **Automatically processing emails** - Extracts tasks from email content using AI
- 🤖 **AI-powered task extraction** - Uses Google Gemini or OpenAI to intelligently identify and categorize tasks
- 📊 **Notion integration** - Syncs tasks to Notion databases for team collaboration
- 👥 **Multi-user support** - Each user gets their own task database and workspace
- 💡 **AI coaching insights** - Provides personalized insights and recommendations
- 🔐 **Secure authentication** - JWT-based user authentication and authorization
- ⚡ **Real-time processing** - Gmail processor runs every 5 minutes via Cloud Scheduler

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **PostgreSQL** (local or Cloud SQL)
- **Redis** (local or Memorystore)
- **Google Cloud account** (for deployment)
- **API Keys:**
  - Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
  - Notion integration token ([Create integration](https://www.notion.so/my-integrations))
  - Gmail app password (for email processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "AI Team Support"
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.production.template .env
   # Edit .env and fill in your API keys and configuration
   ```

5. **Run the application**
   ```bash
   python -m src.api.app_auth
   ```

   The app will be available at `http://localhost:5000`

### Required Environment Variables

See `env.production.template` for all options. Minimum required:

```bash
# API Keys (Required)
NOTION_TOKEN=your_notion_token
GEMINI_API_KEY=your_gemini_key
JWT_SECRET_KEY=your_jwt_secret

# Notion Configuration (Required)
NOTION_DATABASE_ID=your_database_id
NOTION_FEEDBACK_DB_ID=your_feedback_db_id
NOTION_USERS_DB_ID=your_users_db_id
NOTION_PARENT_PAGE_ID=your_parent_page_id

# Database (Required if EMAIL_ARCHIVE_ENABLED=True)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (Required for Celery)
REDIS_URL=redis://host:port/db

# Gmail (Required for email processing)
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

## 📁 Project Structure

```
AI-Team-Support/
├── src/                    # Source code
│   ├── api/               # Flask API layer
│   ├── core/              # Business logic (agents, services, AI)
│   ├── config/            # Configuration
│   ├── plugins/           # Plugin system
│   └── utils/             # Utilities (Gmail processor, etc.)
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── performance/       # Performance tests
├── deployment/            # Deployment scripts
│   ├── deploy-gmail-processor-elegant.sh  # Gmail processor deployment
│   └── cloudbuild-gmail-processor.yaml    # Cloud Build config
├── docs/                  # Documentation
│   ├── GOOGLE_CLOUD_DEPLOYMENT.md
│   ├── testing/
│   └── architecture/
└── scripts/               # Utility scripts
```

For detailed structure, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## 🧪 Testing

Run the test suite:

```bash
# All tests
pytest tests/

# Specific test types
pytest tests/unit/              # Unit tests
pytest tests/integration/       # Integration tests
pytest tests/e2e/               # End-to-end tests

# With coverage
pytest tests/ --cov=src --cov-report=html
```

See [docs/testing/TESTING_GUIDE.md](docs/testing/TESTING_GUIDE.md) for detailed testing instructions.

## 🚀 Deployment

### Google Cloud Run

Deploy the Gmail processor:

```bash
cd deployment
./deploy-gmail-processor-elegant.sh
```

This will:
- Build the Docker image
- Deploy to Cloud Run
- Set up Cloud Scheduler (runs every 5 minutes)
- Configure secrets and environment variables

For full deployment guide, see [docs/GOOGLE_CLOUD_DEPLOYMENT.md](docs/GOOGLE_CLOUD_DEPLOYMENT.md).

### Local Development

Run the Flask app locally:

```bash
python -m src.api.app_auth
```

Run Gmail processor locally:

```bash
python check_gmail_enhanced.py
```

## 📚 Documentation

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed project organization
- **[docs/README.md](docs/README.md)** - Developer environment setup
- **[docs/GOOGLE_CLOUD_DEPLOYMENT.md](docs/GOOGLE_CLOUD_DEPLOYMENT.md)** - Deployment guide
- **[docs/testing/TESTING_GUIDE.md](docs/testing/TESTING_GUIDE.md)** - Testing guide
- **[ONBOARDING.md](ONBOARDING.md)** - New developer onboarding guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## 🔧 Key Features

### Gmail Processing
- Automatically checks Gmail every 5 minutes
- Extracts tasks from email content
- Supports multiple users with separate task databases
- Processes corrections and updates

### AI Task Extraction
- Uses Google Gemini or OpenAI for intelligent task extraction
- Identifies task status, categories, and metadata
- Handles complex email formats and bullet points

### Notion Integration
- Automatic task database creation per user
- Syncs tasks with status, categories, and metadata
- Supports feedback and user management databases

### Authentication & Security
- JWT-based authentication
- Secure password hashing (bcrypt)
- User registration and login endpoints

## 🛠️ Development

### Running Scripts

**Always run scripts as modules from project root:**

```bash
# ✅ Correct
python -m src.utils.gmail_processor

# ❌ Wrong
python src/utils/gmail_processor.py
```

### Import Style

**Always use absolute imports:**

```python
# ✅ Correct
from src.core.agents.task_extraction_agent import TaskExtractionAgent

# ❌ Wrong
from .task_extraction_agent import TaskExtractionAgent
```

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Document functions and classes
- Write tests for new features

## 🐛 Troubleshooting

### Common Issues

**Import errors:**
- Make sure you're running from project root
- Use `python -m` syntax for scripts
- Check that virtual environment is activated

**Database connection errors:**
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL is running
- Ensure database exists

**Gmail processing not working:**
- Verify `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` are set
- Check Gmail app password is enabled
- Review logs: `gcloud logs tail --service=gmail-processor`

**Notion integration issues:**
- Verify `NOTION_TOKEN` is valid
- Check integration has access to databases
- Ensure database IDs are correct

## 📋 Requirements

See [requirements.txt](requirements.txt) for full list. Key dependencies:

- Flask - Web framework
- google-generativeai - Gemini AI integration
- notion-client - Notion API
- SQLAlchemy - Database ORM
- Celery - Task queue
- Redis - Caching and task broker

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📝 License

[Add your license here]

## 🔗 Links

- [Google Cloud Console](https://console.cloud.google.com)
- [Notion API Docs](https://developers.notion.com)
- [Gemini API Docs](https://ai.google.dev/docs)

## 📞 Support

For issues or questions:
1. Check [ONBOARDING.md](ONBOARDING.md) for setup help
2. Review [docs/testing/TESTING_GUIDE.md](docs/testing/TESTING_GUIDE.md) for testing
3. See [docs/GOOGLE_CLOUD_DEPLOYMENT.md](docs/GOOGLE_CLOUD_DEPLOYMENT.md) for deployment issues

---

**Note:** This is a production system with real Gmail and Notion integrations. Always test changes in a development environment first.

# 👋 Onboarding Guide

Welcome to the AI Team Support project! This guide will help you get set up and productive quickly.

## 🎯 Day 1 Checklist

By the end of Day 1, you should be able to:
- [ ] Run the application locally
- [ ] Understand the project structure
- [ ] Run the test suite
- [ ] Make a small change and see it work

## 📋 Prerequisites

Before starting, ensure you have:

- **Python 3.9+** installed (check: `python3 --version`)
- **PostgreSQL** installed and running locally, OR access to Cloud SQL
- **Redis** installed and running locally, OR access to Memorystore
- **Git** installed
- **A text editor/IDE** (VS Code, PyCharm, etc.)

### Required API Keys

You'll need access to:
1. **Notion Integration Token** - From [Notion Integrations](https://www.notion.so/my-integrations)
2. **Google Gemini API Key** - From [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Gmail App Password** - From Gmail settings (if testing email processing)

**Note:** Ask the project maintainer for test/development credentials if you don't have your own.

## 🚀 Step 1: Clone and Setup

### 1.1 Clone the Repository

```bash
git clone https://github.com/agarciangulo/Task-Manager-5.8.git
cd "Task-Manager-5.8"
```

### 1.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify activation (should show venv path)
which python  # On Windows: where python
```

### 1.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Troubleshooting:** If installation fails:
- Check Python version: `python3 --version` (should be 3.9+)
- On macOS, you may need: `xcode-select --install`
- On Linux, install build tools: `sudo apt-get install build-essential python3-dev`

## 🔧 Step 2: Environment Configuration

### 2.1 Copy Environment Template

```bash
cp env.production.template .env
```

### 2.2 Fill in Environment Variables

Edit `.env` with your values:

```bash
# Minimum required for basic functionality
NOTION_TOKEN=secret_...
GEMINI_API_KEY=AIza...
JWT_SECRET_KEY=your-secret-key-here

# Notion Database IDs (ask maintainer or create test databases)
NOTION_DATABASE_ID=1e35c6ec3b80804f922ce6cc63d0c36b
NOTION_FEEDBACK_DB_ID=1cc5c6ec3b8080ab934feb388e729447
NOTION_USERS_DB_ID=2175c6ec3b8080ac9d60c035a3000f52
NOTION_PARENT_PAGE_ID=2175c6ec3b8080d183d0c0e4fb219f9d

# Database (if using email archive)
DATABASE_URL=postgresql://postgres:password@localhost:5432/email_archive

# Redis (if using Celery)
REDIS_URL=redis://localhost:6379/0

# Gmail (optional for local testing)
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Application settings
FLASK_ENV=development
FLASK_DEBUG=1
ENABLE_AUTHENTICATION=True
```

**Important:** Never commit `.env` to git!

### 2.3 Verify Environment Variables

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('NOTION_TOKEN:', 'SET' if os.getenv('NOTION_TOKEN') else 'MISSING')"
```

## ✅ Step 3: Verify Setup

### 3.1 Run Tests

First, let's make sure everything is working:

```bash
# Run a simple test to verify setup
pytest tests/unit/test_service_initialization.py -v
```

If this passes, your basic setup is correct!

### 3.2 Start the Application

```bash
python -m src.api.app_auth
```

You should see output like:
```
Environment Variables Loaded:
GEMINI_API_KEY: AIzaSy...
...
Running on http://127.0.0.1:5000
```

**Test it:** Open `http://localhost:5000` in your browser. You should see the app homepage.

## 📚 Step 4: Understand the Project

### 4.1 Project Overview

This is an **AI-powered task management system** that:
1. **Processes emails** - Checks Gmail every 5 minutes (in production)
2. **Extracts tasks** - Uses AI (Gemini) to identify tasks from email content
3. **Stores in Notion** - Syncs tasks to user-specific Notion databases
4. **Provides insights** - Generates AI coaching insights

### 4.2 Key Directories

```
src/
├── api/              # Flask API endpoints
│   ├── app_auth.py   # Main Flask application
│   └── routes/       # API route blueprints
├── core/
│   ├── agents/       # AI agents (task extraction, etc.)
│   ├── services/     # Business logic layer
│   └── ai/           # AI client code (Gemini/OpenAI)
└── utils/            # Utilities (Gmail processor, etc.)

tests/
├── unit/             # Test individual components
├── integration/      # Test component interactions
└── e2e/              # Test complete workflows
```

### 4.3 Key Concepts

**Service Layer Pattern:**
- Business logic is in `src/core/services/`
- Services are injected via dependency injection
- API routes call services, not direct database access

**AI Client:**
- Located in `src/core/ai_client.py`
- Supports both Gemini (default) and OpenAI
- Configured via `AI_PROVIDER` environment variable

**Gmail Processing:**
- Entry point: `src/utils/gmail_processor_enhanced.py`
- Processes emails every 5 minutes (Cloud Scheduler in production)
- Extracts tasks and syncs to Notion

## 🧪 Step 5: Run Tests

### 5.1 Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### 5.2 Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v
```

### 5.3 Common Test Scenarios

```bash
# Test authentication
pytest tests/unit/test_auth.py -v

# Test Gmail processing
pytest tests/unit/test_gmail_connection.py -v

# Test Notion integration
pytest tests/integration/test_notion_integration.py -v
```

## 🔨 Step 6: Make Your First Change

### 6.1 Simple Task: Add a Log Statement

1. **Find a file to modify:**
   ```bash
   # Open the main app file
   code src/api/app_auth.py  # or use your editor
   ```

2. **Add a log statement:**
   ```python
   # Around line 100, find the Flask app initialization
   app = Flask(__name__)
   
   # Add after it:
   app.logger.info("🚀 Application started by [YOUR_NAME]")
   ```

3. **Test your change:**
   ```bash
   python -m src.api.app_auth
   # Look for your log message in the output
   ```

4. **Run tests to make sure nothing broke:**
   ```bash
   pytest tests/unit/test_service_initialization.py -v
   ```

### 6.2 Test the Change

```bash
# Start the app
python -m src.api.app_auth

# In another terminal, test an endpoint
curl http://localhost:5000/api/health

# You should see your log message in the app output
```

## 🗺️ Step 7: Explore Key Workflows

### 7.1 Email Processing Workflow

1. **Find the Gmail processor:**
   ```bash
   code src/utils/gmail_processor_enhanced.py
   ```

2. **Understand the flow:**
   - `check_gmail_for_updates_enhanced()` - Main entry point
   - Checks Gmail for new emails
   - Processes each email through the task extraction agent
   - Syncs tasks to Notion

3. **Test locally (optional):**
   ```bash
   python check_gmail_enhanced.py
   ```

### 7.2 Task Extraction Workflow

1. **Find the task extraction agent:**
   ```bash
   code src/core/agents/task_extraction_agent.py
   ```

2. **Trace the flow:**
   - Agent receives email content
   - Calls AI client to extract tasks
   - Processes and validates tasks
   - Returns structured task data

### 7.3 Notion Sync Workflow

1. **Find the task service:**
   ```bash
   code src/core/services/task_management_service.py
   ```

2. **See how tasks are synced:**
   - Service receives tasks
   - Connects to Notion API
   - Creates/updates task entries
   - Handles errors and retries

## 🐛 Common Issues & Solutions

### Issue: Import Errors

**Symptoms:** `ModuleNotFoundError` or `ImportError`

**Solution:**
```bash
# Make sure you're in project root
pwd  # Should show "AI Team Support"

# Make sure venv is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database Connection Errors

**Symptoms:** `psycopg2.OperationalError` or connection refused

**Solution:**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# If not running, start it:
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Verify DATABASE_URL in .env is correct
```

### Issue: Redis Connection Errors

**Symptoms:** `redis.ConnectionError`

**Solution:**
```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# If not running, start it:
# macOS: brew services start redis
# Linux: sudo systemctl start redis
```

### Issue: Notion API Errors

**Symptoms:** `401 Unauthorized` or `403 Forbidden`

**Solution:**
- Verify `NOTION_TOKEN` is correct
- Check integration has access to required databases
- Ensure database IDs in `.env` are correct
- Test token: `curl -H "Authorization: Bearer $NOTION_TOKEN" https://api.notion.com/v1/users/me`

### Issue: Gemini API Errors

**Symptoms:** `403` or quota errors

**Solution:**
- Verify `GEMINI_API_KEY` is correct
- Check API quota in [Google Cloud Console](https://console.cloud.google.com)
- Try regenerating the API key

## 📖 Next Steps

### Day 2-3: Deeper Understanding

1. **Read the architecture:**
   - Review `docs/architecture/` (if available)
   - Study `PROJECT_STRUCTURE.md`

2. **Understand the test suite:**
   - Read `docs/testing/TESTING_GUIDE.md`
   - Explore test files in `tests/`

3. **Study a feature end-to-end:**
   - Pick one feature (e.g., task extraction)
   - Trace it from API → Service → Agent → Notion
   - Write a small test for it

### Week 1: Make Real Contributions

1. **Pick a good first issue:**
   - Look for "good first issue" labels
   - Start with documentation improvements
   - Fix small bugs

2. **Follow contribution workflow:**
   - Read [CONTRIBUTING.md](CONTRIBUTING.md)
   - Create a feature branch
   - Write tests
   - Submit a PR

## 🆘 Getting Help

### Resources

- **Documentation:** Check `docs/` directory
- **Code examples:** Look at existing tests in `tests/`
- **Project structure:** See `PROJECT_STRUCTURE.md`

### Ask Questions

- Check existing issues/PRs
- Ask in team chat (if available)
- Review code comments and docstrings

## ✅ Onboarding Complete!

Once you can:
- ✅ Run the app locally
- ✅ Run tests successfully
- ✅ Make a small change
- ✅ Understand the basic architecture

**You're ready to contribute!** 🎉

Check out [CONTRIBUTING.md](CONTRIBUTING.md) for next steps.






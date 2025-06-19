"""
Staging environment configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

# Debug settings
DEBUG = True  # Keep debug on for staging
TESTING = False

# API Configuration
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
NOTION_FEEDBACK_DB_ID = os.getenv('NOTION_FEEDBACK_DB_ID')

# Application Settings
SIMILARITY_THRESHOLD = 0.70
ENABLE_TASK_VALIDATION = True
ENABLE_CHAT_VERIFICATION = True
MIN_TASK_LENGTH = 3
DAYS_THRESHOLD = 2

# AI Configuration
AI_PROVIDER = 'gemini'
CHAT_MODEL = 'gpt-3.5-turbo'  # Using same model as development for testing
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///staging.db')  # Fallback to SQLite if no env var

# Logging
LOG_LEVEL = 'DEBUG'  # Keep debug logging for staging
LOG_FILE = 'logs/staging.log' 
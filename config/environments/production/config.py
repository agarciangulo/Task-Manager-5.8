"""
Production environment configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Debug settings
DEBUG = False
TESTING = False

# API Configuration
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
NOTION_FEEDBACK_DB_ID = os.getenv('NOTION_FEEDBACK_DB_ID')

# Application Settings
SIMILARITY_THRESHOLD = 0.75  # Slightly higher threshold for production
ENABLE_TASK_VALIDATION = True
ENABLE_CHAT_VERIFICATION = True
MIN_TASK_LENGTH = 3
DAYS_THRESHOLD = 2

# AI Configuration
AI_PROVIDER = 'gemini'
CHAT_MODEL = 'gpt-4'  # Using GPT-4 for production
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

# Database
DATABASE_URL = os.getenv('DATABASE_URL')  # Use environment variable for production database

# Logging
LOG_LEVEL = 'INFO'  # Less verbose logging in production
LOG_FILE = 'logs/production.log' 
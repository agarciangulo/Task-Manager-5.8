"""
Configuration settings for Task Manager.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Notion API Configuration
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
NOTION_FEEDBACK_DB_ID = os.getenv('NOTION_FEEDBACK_DB_ID')

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Application Settings
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.70'))
ENABLE_TASK_VALIDATION = os.getenv('ENABLE_TASK_VALIDATION', 'True').lower() == 'true'
ENABLE_CHAT_VERIFICATION = os.getenv('ENABLE_CHAT_VERIFICATION', 'True').lower() == 'true'
MIN_TASK_LENGTH = int(os.getenv('MIN_TASK_LENGTH', '3'))
DAYS_THRESHOLD = int(os.getenv('DAYS_THRESHOLD', '2'))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False') == 'True'

# File paths
EMBEDDING_CACHE_PATH = os.getenv('EMBEDDING_CACHE_PATH', 'embedding_cache.db')

# Cache settings
MAX_CACHE_ENTRIES = int(os.getenv('MAX_CACHE_ENTRIES', '10000'))

# AI Configuration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')  # Changed default to gemini
CHAT_MODEL = os.getenv('CHAT_MODEL', 'gemini-1.5-flash')  # Changed default to Gemini model
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'  # Lightweight embedding model
AI_MODEL = CHAT_MODEL  # For backward compatibility

# OpenAI configuration
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')

# Gemini configuration
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
GEMINI_EMBEDDING_MODEL = os.getenv('GEMINI_EMBEDDING_MODEL', 'embedding-001')

# Hugging Face configuration
HF_MODEL = os.getenv('HF_MODEL', 'mistralai/Mistral-7B-Instruct-v0.2')
HF_EMBEDDING_MODEL = os.getenv('HF_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')  # Add token support

# Task matching settings
USE_AI_MATCHING = os.getenv('USE_AI_MATCHING', 'True').lower() == 'true'

# Validate required environment variables
required_vars = [
    'NOTION_TOKEN',
    'NOTION_DATABASE_ID',
    'NOTION_FEEDBACK_DB_ID'
]

# Add API key to required vars based on AI provider
if AI_PROVIDER == 'openai':
    required_vars.append('OPENAI_API_KEY')
elif AI_PROVIDER == 'gemini':
    required_vars.append('GEMINI_API_KEY')

missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print("Warning: Missing required environment variables:")
    for var in missing_vars:
        print(f"  - {var}")

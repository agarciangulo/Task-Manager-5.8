"""
Main application entry point for Task Manager.
"""
import os
import sys
import subprocess

# First make sure setuptools is installed
try:
    import pkg_resources
except ImportError:
    print("Installing setuptools...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
    import pkg_resources
    print("setuptools installed successfully.")

# List of required packages
REQUIRED_PACKAGES = [
    "openai>=1.0.0",  # Using the new OpenAI API
    "notion-client",
    "pandas",
    "python-dateutil",
    "gradio",
    "scikit-learn",
    "numpy",
    "flask",  # Only needed if using the Flask version
    "python-dotenv"  # For .env file support
]

def install_requirements():
    """Install required packages if not already installed."""
    print("Checking and installing required packages...")
    
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = []
    
    for package in REQUIRED_PACKAGES:
        package_name = package.split('==')[0] if '==' in package else package
        if package_name.lower() not in installed:
            missing.append(package)
    
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("All required packages installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            print("Please install the following packages manually:")
            for pkg in missing:
                print(f"  - {pkg}")
            sys.exit(1)
    else:
        print("All required packages already installed.")

# Run the installation function
install_requirements()

from src.core.ui.interface import create_ui
from src.core.notion_service import NotionService
from src.config.settings import (
    OPENAI_API_KEY, 
    NOTION_TOKEN, 
    NOTION_DATABASE_ID, 
    NOTION_FEEDBACK_DB_ID
)

# Import from the new structure
from src.core.agents.notion_agent import NotionAgent
from src.core.agents.task_extraction_agent import TaskExtractionAgent
from src.core.agents.task_processing_agent import TaskProcessingAgent
from src.core.ai.analyzers import TaskAnalyzer, ProjectAnalyzer
from src.core.ai.insights import get_project_insight
from core import identify_stale_tasks, list_all_categories

# Import from plugins
from plugins import initialize_all_plugins, plugin_manager

# Import from config
from src.config.settings import (
    GEMINI_API_KEY,
    NOTION_TOKEN,
    NOTION_DATABASE_ID,
    NOTION_FEEDBACK_DB_ID,
    SIMILARITY_THRESHOLD,
    ENABLE_TASK_VALIDATION,
    ENABLE_CHAT_VERIFICATION,
    DEBUG_MODE
)

def check_environment():
    """Check if all required API keys are set."""
    from src.config.settings import (
        OPENAI_API_KEY, 
        NOTION_TOKEN, 
        NOTION_DATABASE_ID, 
        NOTION_FEEDBACK_DB_ID
    )
    
    missing_vars = []
    
    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    
    if not NOTION_TOKEN:
        missing_vars.append("NOTION_TOKEN")
    
    if not NOTION_DATABASE_ID:
        missing_vars.append("NOTION_DATABASE_ID")
    
    if not NOTION_FEEDBACK_DB_ID:
        missing_vars.append("NOTION_FEEDBACK_DB_ID")
    
    if missing_vars:
        print("❌ Missing required API keys:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these values directly in config.py")
        return False
    
    return True

def main():
    """Main application entry point."""
    # Print welcome message
    print("\n========================================")
    print("🚀 Starting Task Manager Application")
    print("========================================\n")
    
    # Check environment variables
    if not check_environment():
        sys.exit(1)
    
    # Initialize NotionService and validate connection
    notion_service = NotionService()
    if not notion_service.validate_connection():
        print("❌ Failed to connect to Notion. Please check your credentials.")
        sys.exit(1)
    
    # Create and launch UI
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=8080)

if __name__ == "__main__":
    main()
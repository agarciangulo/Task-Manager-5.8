#!/usr/bin/env python3
"""
Test script to verify the new directory structure works correctly.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all key modules can be imported from the new structure."""
    print("Testing new directory structure...")
    
    try:
        # Test core imports
        print("✅ Testing core imports...")
        import core
        import config
        import plugins
        
        # Test specific modules
        print("✅ Testing specific modules...")
        from src.core.models.user import User
        from src.core.models.task import Task, TaskStatus
        from src.core.services.auth_service import AuthService
        from src.core.services.email_archive_service import EmailArchiveService
        from src.core.services.user_task_service import UserTaskService
        from src.core.ai import analyzers, extractors, insights
        from src.core.agents.notion_agent import NotionAgent
        from src.core.agents.task_extraction_agent import TaskExtractionAgent
        from src.core.agents.task_processing_agent import TaskProcessingAgent
        from src.core.adapters.plugin_base import PluginBase
        from src.core.adapters.plugin_manager import PluginManager
        from src.core.security.jwt_utils import JWTManager
        from src.core.knowledge.knowledge_base import KnowledgeBase
        from src.core.knowledge.consultant_knowledge import ConsultantKnowledge
        from src.core.chat.session import ChatSession
        from src.core.logging.logging_config import get_logger
        from src.core.exceptions import AgentError
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config():
    """Test that configuration is accessible."""
    try:
        print("✅ Testing configuration...")
        from src.config.settings import (
            NOTION_TOKEN, GEMINI_API_KEY, AI_PROVIDER, 
            DEBUG_MODE, ENABLE_AUTHENTICATION
        )
        print("✅ Configuration accessible!")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing new directory structure...")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_config()
    
    print("=" * 50)
    if success:
        print("✅ All tests passed! New structure is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.") 
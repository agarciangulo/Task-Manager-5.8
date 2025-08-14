#!/usr/bin/env python3
"""
Test script to verify Celery configuration for correction tasks.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_celery_config():
    """Test that Celery configuration is working properly."""
    try:
        from src.core.services.celery_config import celery_app
        print("✅ Successfully imported main Celery app")
        
        # Check if correction tasks are registered
        registered_tasks = celery_app.tasks.keys()
        correction_tasks = [task for task in registered_tasks if 'correction' in task]
        
        print(f"📋 Found {len(correction_tasks)} correction-related tasks:")
        for task in correction_tasks:
            print(f"   - {task}")
        
        # Test importing correction tasks module
        from src.core.tasks.correction_tasks import process_correction, cleanup_old_correction_logs
        print("✅ Successfully imported correction task functions")
        
        # Check if tasks are properly decorated
        if hasattr(process_correction, 'delay'):
            print("✅ process_correction task is properly decorated")
        else:
            print("❌ process_correction task is not properly decorated")
            
        if hasattr(cleanup_old_correction_logs, 'delay'):
            print("✅ cleanup_old_correction_logs task is properly decorated")
        else:
            print("❌ cleanup_old_correction_logs task is not properly decorated")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_celery_app_consistency():
    """Test that all modules use the same Celery app instance."""
    try:
        from src.core.services.celery_config import celery_app as main_app
        from src.core.tasks.correction_tasks import celery_app as correction_app
        
        if main_app is correction_app:
            print("✅ All modules use the same Celery app instance")
            return True
        else:
            print("❌ Different Celery app instances detected")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Celery app consistency: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Celery Configuration...")
    print("=" * 50)
    
    success1 = test_celery_config()
    success2 = test_celery_app_consistency()
    
    print("=" * 50)
    if success1 and success2:
        print("✅ All Celery configuration tests passed!")
    else:
        print("❌ Some Celery configuration tests failed!")
        sys.exit(1) 
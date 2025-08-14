#!/usr/bin/env python3
"""
Debug script to investigate Celery task registration.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_celery_tasks():
    """Debug Celery task registration."""
    print("🔍 Debugging Celery Task Registration...")
    print("=" * 50)
    
    try:
        # Import the Celery app
        from src.core.services.celery_config import celery_app
        print("✅ Successfully imported Celery app")
        
        # Check all registered tasks
        all_tasks = list(celery_app.tasks.keys())
        print(f"📋 Total registered tasks: {len(all_tasks)}")
        
        # Look for correction tasks specifically
        correction_tasks = [task for task in all_tasks if 'correction' in task.lower()]
        print(f"🔍 Correction-related tasks found: {len(correction_tasks)}")
        
        if correction_tasks:
            print("📝 Correction tasks:")
            for task in correction_tasks:
                print(f"   - {task}")
        else:
            print("❌ No correction tasks found")
            
        # Check if the correction tasks module can be imported
        print("\n📋 Testing correction tasks module import...")
        try:
            from src.core.tasks.correction_tasks import process_correction, cleanup_old_correction_logs
            print("✅ Correction tasks module imported successfully")
            
            # Check if tasks are decorated
            if hasattr(process_correction, 'delay'):
                print("✅ process_correction is properly decorated")
            else:
                print("❌ process_correction is not properly decorated")
                
            if hasattr(cleanup_old_correction_logs, 'delay'):
                print("✅ cleanup_old_correction_logs is properly decorated")
            else:
                print("❌ cleanup_old_correction_logs is not properly decorated")
                
        except Exception as e:
            print(f"❌ Error importing correction tasks: {e}")
            
        # Check Celery app configuration
        print("\n📋 Checking Celery app configuration...")
        print(f"   Broker URL: {celery_app.conf.broker_url}")
        print(f"   Result Backend: {celery_app.conf.result_backend}")
        print(f"   Include modules: {celery_app.conf.include}")
        
        # Try to manually register the tasks
        print("\n📋 Attempting manual task registration...")
        try:
            celery_app.autodiscover_tasks(['src.core.tasks'])
            print("✅ Auto-discovery completed")
            
            # Check again
            all_tasks_after = list(celery_app.tasks.keys())
            correction_tasks_after = [task for task in all_tasks_after if 'correction' in task.lower()]
            print(f"📋 Correction tasks after auto-discovery: {len(correction_tasks_after)}")
            
            if correction_tasks_after:
                print("📝 Correction tasks found:")
                for task in correction_tasks_after:
                    print(f"   - {task}")
                    
        except Exception as e:
            print(f"❌ Auto-discovery error: {e}")
            
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_celery_tasks() 
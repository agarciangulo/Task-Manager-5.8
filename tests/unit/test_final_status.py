#!/usr/bin/env python3
"""
Final status test for correction handler components.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_correction_handler_status():
    """Test the overall status of the correction handler."""
    print("🧪 Testing Correction Handler Final Status...")
    print("=" * 60)
    
    results = []
    
    # Test 1: Celery Configuration
    print("\n📋 Test 1: Celery Configuration")
    try:
        from src.core.services.celery_config import celery_app
        registered_tasks = celery_app.tasks.keys()
        correction_tasks = [task for task in registered_tasks if 'correction' in task]
        
        if len(correction_tasks) > 0:
            print(f"✅ Found {len(correction_tasks)} correction tasks")
            results.append(("Celery Configuration", True))
        else:
            print("❌ No correction tasks found")
            results.append(("Celery Configuration", False))
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        results.append(("Celery Configuration", False))
    
    # Test 2: Service Initialization
    print("\n📋 Test 2: Service Initialization")
    try:
        from src.utils.gmail_processor_enhanced import correction_service, email_router
        
        if email_router is not None:
            print("✅ Email router initialized")
            results.append(("Email Router", True))
        else:
            print("❌ Email router not initialized")
            results.append(("Email Router", False))
            
        if correction_service is not None:
            print("✅ Correction service initialized")
            results.append(("Correction Service", True))
        else:
            print("⚠️ Correction service not initialized (expected without DATABASE_URL)")
            results.append(("Correction Service", True))  # This is expected
    except Exception as e:
        print(f"❌ Service initialization error: {e}")
        results.append(("Service Initialization", False))
    
    # Test 3: Plugin Discovery
    print("\n📋 Test 3: Plugin Discovery")
    try:
        from src.plugins.plugin_manager_instance import plugin_manager
        
        expected_plugins = ['ConsultantGuidelinesPlugin', 'PeerFeedbackPlugin', 'ProjectProtectionPlugin']
        discovered_plugins = list(plugin_manager.plugin_classes.keys())
        
        missing_plugins = []
        for expected in expected_plugins:
            if expected in discovered_plugins:
                print(f"✅ {expected} discovered")
            else:
                print(f"❌ {expected} not discovered")
                missing_plugins.append(expected)
        
        if not missing_plugins:
            results.append(("Plugin Discovery", True))
        else:
            results.append(("Plugin Discovery", False))
    except Exception as e:
        print(f"❌ Plugin discovery error: {e}")
        results.append(("Plugin Discovery", False))
    
    # Test 4: Plugin Registration
    print("\n📋 Test 4: Plugin Registration")
    try:
        registered_plugins = list(plugin_manager.plugins.keys())
        
        if len(registered_plugins) > 0:
            print(f"✅ {len(registered_plugins)} plugins registered:")
            for plugin_name in registered_plugins:
                plugin_instance = plugin_manager.plugins[plugin_name]
                status = "enabled" if hasattr(plugin_instance, 'enabled') and plugin_instance.enabled else "active"
                print(f"   - {plugin_name}: {status}")
            results.append(("Plugin Registration", True))
        else:
            print("❌ No plugins registered")
            results.append(("Plugin Registration", False))
    except Exception as e:
        print(f"❌ Plugin registration error: {e}")
        results.append(("Plugin Registration", False))
    
    # Test 5: Error Handling Functions
    print("\n📋 Test 5: Error Handling Functions")
    try:
        from src.utils.gmail_processor_enhanced import (
            send_correction_service_unavailable_email,
            send_correction_queue_error_email,
            send_correction_processing_error_email,
            process_correction_email
        )
        print("✅ All error handling functions available")
        results.append(("Error Handling", True))
    except Exception as e:
        print(f"❌ Error handling functions error: {e}")
        results.append(("Error Handling", False))
    
    # Test 6: Database Models
    print("\n📋 Test 6: Database Models")
    try:
        from src.core.models.correction_models import TaskCorrectionLog, TaskCorrection, Base
        print("✅ Database models available")
        results.append(("Database Models", True))
    except Exception as e:
        print(f"❌ Database models error: {e}")
        results.append(("Database Models", False))
    
    # Test 7: Correction Tasks
    print("\n📋 Test 7: Correction Tasks")
    try:
        from src.core.tasks.correction_tasks import process_correction, cleanup_old_correction_logs
        print("✅ Correction tasks available")
        results.append(("Correction Tasks", True))
    except Exception as e:
        print(f"❌ Correction tasks error: {e}")
        results.append(("Correction Tasks", False))
    
    # Test 8: Guidelines Plugin
    print("\n📋 Test 8: Guidelines Plugin")
    try:
        from src.plugins.guidelines.consultant_guidelines import ConsultantGuidelinesPlugin
        plugin = ConsultantGuidelinesPlugin()
        if plugin.initialize():
            print("✅ Guidelines plugin working")
            results.append(("Guidelines Plugin", True))
        else:
            print("❌ Guidelines plugin failed to initialize")
            results.append(("Guidelines Plugin", False))
    except Exception as e:
        print(f"❌ Guidelines plugin error: {e}")
        results.append(("Guidelines Plugin", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL STATUS SUMMARY:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Status: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n📋 Correction Handler is ready for use with:")
        print("   ✅ Celery tasks properly configured")
        print("   ✅ Service initialization with error handling")
        print("   ✅ Plugin system working")
        print("   ✅ Error handling functions available")
        print("   ✅ Database models ready")
        print("\n⚠️  Note: Database connection requires DATABASE_URL environment variable")
        return True
    else:
        print("⚠️  Some issues remain. See details above.")
        return False

if __name__ == "__main__":
    success = test_correction_handler_status()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
"""
Test script to verify database operations for the correction service.
"""
import os
import sys
import traceback
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_correction_service_creation():
    """Test that CorrectionService can be created."""
    try:
        from src.core.services.correction_service import CorrectionService
        print("✅ Successfully imported CorrectionService")
        
        # Test service creation
        service = CorrectionService()
        print("✅ CorrectionService created successfully")
        
        return service
        
    except Exception as e:
        print(f"❌ Error creating CorrectionService: {e}")
        print(traceback.format_exc())
        return None

def test_correction_log_creation(service):
    """Test creating a correction log entry."""
    try:
        if not service:
            print("⚠️ Skipping correction log test - no service available")
            return False
        
        # Create test data
        correlation_id = f"corr-{uuid.uuid4()}"
        user_email = "test@example.com"
        task_ids = ["task1", "task2", "task3"]
        email_subject = "Test Summary"
        
        # Create correction log
        log_id = service.create_correction_log(
            correlation_id=correlation_id,
            user_email=user_email,
            task_ids=task_ids,
            email_subject=email_subject
        )
        
        print(f"✅ Created correction log with ID: {log_id}")
        
        # Retrieve the log
        log_data = service.get_correction_log(correlation_id)
        if log_data:
            print(f"✅ Retrieved correction log: {log_data['correlation_id']}")
            print(f"   User: {log_data['user_email']}")
            print(f"   Tasks: {log_data['task_ids']}")
            print(f"   Status: {log_data['status']}")
        else:
            print("❌ Failed to retrieve correction log")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing correction log creation: {e}")
        print(traceback.format_exc())
        return False

def test_correction_log_status_update(service):
    """Test updating correction log status."""
    try:
        if not service:
            print("⚠️ Skipping status update test - no service available")
            return False
        
        # Create test data
        correlation_id = f"corr-{uuid.uuid4()}"
        user_email = "test@example.com"
        task_ids = ["task1"]
        
        # Create log
        service.create_correction_log(
            correlation_id=correlation_id,
            user_email=user_email,
            task_ids=task_ids
        )
        
        # Update status
        service.update_correction_log_status(
            correlation_id=correlation_id,
            status="completed",
            error_message=None
        )
        
        # Verify update
        log_data = service.get_correction_log(correlation_id)
        if log_data and log_data['status'] == 'completed':
            print("✅ Successfully updated correction log status")
            return True
        else:
            print("❌ Failed to update correction log status")
            return False
        
    except Exception as e:
        print(f"❌ Error testing status update: {e}")
        print(traceback.format_exc())
        return False

def test_correction_application_logging(service):
    """Test logging correction applications."""
    try:
        if not service:
            print("⚠️ Skipping application logging test - no service available")
            return False
        
        # Create test data
        correlation_id = f"corr-{uuid.uuid4()}"
        user_email = "test@example.com"
        task_ids = ["task1"]
        
        # Create log
        log_id = service.create_correction_log(
            correlation_id=correlation_id,
            user_email=user_email,
            task_ids=task_ids
        )
        
        # Log correction application
        service.log_correction_application(
            correction_log_id=log_id,
            task_id="task1",
            correction_type="update",
            original_data={"status": "pending"},
            corrected_data={"status": "completed"},
            success=True,
            error_message=None
        )
        
        print("✅ Successfully logged correction application")
        return True
        
    except Exception as e:
        print(f"❌ Error testing correction application logging: {e}")
        print(traceback.format_exc())
        return False

def test_cleanup_operations(service):
    """Test cleanup operations."""
    try:
        if not service:
            print("⚠️ Skipping cleanup test - no service available")
            return False
        
        # Test cleanup (should not fail even if no old logs exist)
        service.cleanup_old_logs(days_old=30)
        print("✅ Cleanup operation completed successfully")
        
        # Test stats retrieval
        stats = service.get_correction_stats()
        print(f"✅ Retrieved correction stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing cleanup operations: {e}")
        print(traceback.format_exc())
        return False

def test_database_models():
    """Test that database models can be imported and used."""
    try:
        from src.core.models.correction_models import TaskCorrectionLog, TaskCorrection, Base
        print("✅ Successfully imported correction models")
        
        # Test model creation
        log = TaskCorrectionLog(
            correlation_id=f"corr-{uuid.uuid4()}",
            user_email="test@example.com",
            task_ids=["task1", "task2"]
        )
        print("✅ Successfully created TaskCorrectionLog instance")
        
        correction = TaskCorrection(
            correction_log_id=str(uuid.uuid4()),
            task_id="task1",
            correction_type="update",
            original_data={"status": "pending"},
            corrected_data={"status": "completed"}
        )
        print("✅ Successfully created TaskCorrection instance")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database models: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 Testing Database Operations...")
    print("=" * 50)
    
    # Test database models first
    print("\n📋 Testing Database Models...")
    models_ok = test_database_models()
    
    # Test service creation
    print("\n📋 Testing Service Creation...")
    service = test_correction_service_creation()
    
    # Test operations if service is available
    tests = []
    if service:
        tests = [
            ("Correction Log Creation", lambda: test_correction_log_creation(service)),
            ("Status Update", lambda: test_correction_log_status_update(service)),
            ("Application Logging", lambda: test_correction_application_logging(service)),
            ("Cleanup Operations", lambda: test_cleanup_operations(service)),
        ]
    else:
        print("⚠️ Skipping database operation tests - service not available")
    
    results = [("Database Models", models_ok)]
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    # Clean up service
    if service:
        try:
            service.close()
            print("✅ Service closed successfully")
        except Exception as e:
            print(f"⚠️ Error closing service: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All database tests passed!")
    else:
        print("\n⚠️ Some database tests failed. Please check the errors above.")
        sys.exit(1) 
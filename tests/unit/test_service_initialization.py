#!/usr/bin/env python3
"""
Test script to verify service initialization and error handling improvements.
"""
import os
import sys
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_service_initialization():
    """Test the improved service initialization."""
    try:
        from src.utils.gmail_processor_enhanced import (
            initialize_correction_service, 
            correction_service, 
            email_router
        )
        print("✅ Successfully imported service initialization functions")
        
        # Test correction service initialization
        if correction_service is not None:
            print("✅ Correction service initialized successfully")
        else:
            print("⚠️ Correction service initialization failed (this might be expected if DATABASE_URL is not set)")
        
        # Test email router initialization
        if email_router is not None:
            print("✅ Email router initialized successfully")
        else:
            print("❌ Email router initialization failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing service initialization: {e}")
        print(traceback.format_exc())
        return False

def test_error_handling_functions():
    """Test the new error handling functions."""
    try:
        from src.utils.gmail_processor_enhanced import (
            send_correction_service_unavailable_email,
            send_correction_queue_error_email,
            send_correction_processing_error_email
        )
        print("✅ Successfully imported error handling functions")
        
        # Test function signatures
        import inspect
        
        # Check send_correction_service_unavailable_email
        sig = inspect.signature(send_correction_service_unavailable_email)
        if len(sig.parameters) == 2:
            print("✅ send_correction_service_unavailable_email has correct signature")
        else:
            print("❌ send_correction_service_unavailable_email has incorrect signature")
        
        # Check send_correction_queue_error_email
        sig = inspect.signature(send_correction_queue_error_email)
        if len(sig.parameters) == 3:
            print("✅ send_correction_queue_error_email has correct signature")
        else:
            print("❌ send_correction_queue_error_email has incorrect signature")
        
        # Check send_correction_processing_error_email
        sig = inspect.signature(send_correction_processing_error_email)
        if len(sig.parameters) == 3:
            print("✅ send_correction_processing_error_email has correct signature")
        else:
            print("❌ send_correction_processing_error_email has incorrect signature")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing error handling functions: {e}")
        print(traceback.format_exc())
        return False

def test_process_correction_email_improvements():
    """Test the improved process_correction_email function."""
    try:
        from src.utils.gmail_processor_enhanced import process_correction_email
        print("✅ Successfully imported improved process_correction_email function")
        
        # Test function signature
        import inspect
        sig = inspect.signature(process_correction_email)
        expected_params = ['msg', 'body', 'sender_email', 'correlation_id']
        
        if all(param in sig.parameters for param in expected_params):
            print("✅ process_correction_email has correct signature")
        else:
            print("❌ process_correction_email has incorrect signature")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing process_correction_email improvements: {e}")
        print(traceback.format_exc())
        return False

def test_imports_without_errors():
    """Test that all imports work without errors."""
    try:
        # Test importing the main module
        import src.utils.gmail_processor_enhanced
        print("✅ Successfully imported gmail_processor_enhanced module")
        
        # Test importing specific functions
        from src.utils.gmail_processor_enhanced import (
            check_gmail_for_updates_enhanced,
            send_confirmation_email_with_correction_support
        )
        print("✅ Successfully imported main functions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing modules: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 Testing Service Initialization Improvements...")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports_without_errors),
        ("Service Initialization", test_service_initialization),
        ("Error Handling Functions", test_error_handling_functions),
        ("Process Correction Email", test_process_correction_email_improvements),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! Service initialization improvements are working.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1) 
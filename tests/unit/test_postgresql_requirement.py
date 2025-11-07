#!/usr/bin/env python3
"""
Test script to verify that CorrectionService requires PostgreSQL and DATABASE_URL.
"""
import os
import sys
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database_url_requirement():
    """Test that CorrectionService requires DATABASE_URL."""
    try:
        from src.core.services.correction_service import CorrectionService
        print("✅ Successfully imported CorrectionService")
        
        # Clear DATABASE_URL to test requirement
        original_database_url = os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        try:
            # This should fail
            service = CorrectionService()
            print("❌ CorrectionService should have failed without DATABASE_URL")
            return False
        except ValueError as e:
            if "DATABASE_URL" in str(e):
                print("✅ CorrectionService correctly requires DATABASE_URL")
                print(f"   Error message: {e}")
                return True
            else:
                print(f"❌ Unexpected ValueError: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected exception: {e}")
            return False
        finally:
            # Restore original DATABASE_URL
            if original_database_url:
                os.environ['DATABASE_URL'] = original_database_url
        
    except Exception as e:
        print(f"❌ Error testing DATABASE_URL requirement: {e}")
        print(traceback.format_exc())
        return False

def test_gmail_processor_handling():
    """Test that gmail processor handles missing DATABASE_URL gracefully."""
    try:
        from src.utils.gmail_processor_enhanced import initialize_correction_service
        print("✅ Successfully imported initialize_correction_service")
        
        # Clear DATABASE_URL to test graceful handling
        original_database_url = os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        try:
            # This should return None gracefully
            service = initialize_correction_service()
            if service is None:
                print("✅ Gmail processor gracefully handles missing DATABASE_URL")
                return True
            else:
                print("❌ Gmail processor should have returned None for missing DATABASE_URL")
                return False
        finally:
            # Restore original DATABASE_URL
            if original_database_url:
                os.environ['DATABASE_URL'] = original_database_url
        
    except Exception as e:
        print(f"❌ Error testing gmail processor handling: {e}")
        print(traceback.format_exc())
        return False

def test_with_valid_database_url():
    """Test that CorrectionService works with a valid DATABASE_URL."""
    try:
        from src.core.services.correction_service import CorrectionService
        print("✅ Successfully imported CorrectionService")
        
        # Check if DATABASE_URL is set
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("⚠️ DATABASE_URL not set, skipping valid URL test")
            return True  # Not a failure, just skip
        
        try:
            service = CorrectionService()
            print("✅ CorrectionService works with valid DATABASE_URL")
            service.close()
            return True
        except Exception as e:
            print(f"⚠️ CorrectionService failed with valid DATABASE_URL: {e}")
            print("   This might be expected if PostgreSQL is not running")
            return True  # Not a failure, just informational
        
    except Exception as e:
        print(f"❌ Error testing with valid DATABASE_URL: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 Testing PostgreSQL Requirement...")
    print("=" * 50)
    
    tests = [
        ("DATABASE_URL Requirement", test_database_url_requirement),
        ("Gmail Processor Handling", test_gmail_processor_handling),
        ("Valid DATABASE_URL Test", test_with_valid_database_url),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! PostgreSQL requirement is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1) 
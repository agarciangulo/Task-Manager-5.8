#!/usr/bin/env python3
"""
Local test script to verify the Notion query fix works.
This tests the auth_service user lookup without deploying.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_user_lookup():
    """Test that we can look up a user from Notion."""
    print("=" * 60)
    print("TESTING NOTION QUERY FIX")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        print("\n1. Initializing AuthService...")
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        print("   ✅ AuthService initialized")
        
        # Test with the email you're using
        test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
        print(f"\n2. Looking up user: {test_email}...")
        
        user = auth_service.get_user_by_email(test_email)
        
        if user:
            print(f"   ✅ User found!")
            print(f"      - Name: {user.full_name}")
            print(f"      - User ID: {user.user_id}")
            print(f"      - Task Database ID: {user.task_database_id}")
            print(f"      - Role: {user.role}")
            print(f"      - Is Active: {user.is_active}")
            return True
        else:
            print(f"   ❌ User not found for {test_email}")
            print(f"      Make sure this email is registered in the Notion users database")
            return False
            
    except AttributeError as e:
        if 'query' in str(e):
            print(f"\n❌ FAILED: Still using old databases.query() method")
            print(f"   Error: {e}")
            print(f"\n   The fix wasn't applied correctly!")
            return False
        else:
            print(f"\n❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notion_client_methods():
    """Test what methods are available on the Notion client."""
    print("\n" + "=" * 60)
    print("TESTING NOTION CLIENT METHODS")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        # Don't need real token for this test
        c = Client(auth='test-token')
        
        print("\n1. Checking databases object...")
        print(f"   Type: {type(c.databases)}")
        print(f"   Has 'query' method: {hasattr(c.databases, 'query')}")
        print(f"   Available methods: {[m for m in dir(c.databases) if not m.startswith('_')]}")
        
        print("\n2. Checking client object...")
        print(f"   Has 'request' method: {hasattr(c, 'request')}")
        if hasattr(c, 'request'):
            import inspect
            sig = inspect.signature(c.request)
            print(f"   Request signature: {sig}")
        
        print("\n✅ Notion client check complete")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_request_method_syntax():
    """Test that the request method syntax is correct."""
    print("\n" + "=" * 60)
    print("TESTING REQUEST METHOD SYNTAX")
    print("=" * 60)
    
    try:
        from notion_client import Client
        import inspect
        
        c = Client(auth='test-token')
        
        # Get the signature
        sig = inspect.signature(c.request)
        print(f"\nRequest method signature:")
        print(f"   {sig}")
        
        # Check parameter order
        params = list(sig.parameters.keys())
        print(f"\nParameter order: {params}")
        
        # Expected: path, method, ...
        if params[0] == 'path' and params[1] == 'method':
            print("   ✅ Parameter order is correct (path, method)")
            return True
        else:
            print(f"   ❌ Unexpected parameter order!")
            print(f"      Expected: path, method, ...")
            print(f"      Got: {params}")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Notion Query Fix Locally\n")
    
    # Run tests
    test1 = test_notion_client_methods()
    test2 = test_request_method_syntax()
    test3 = test_user_lookup()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Notion Client Methods: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Request Method Syntax: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"User Lookup: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if test1 and test2 and test3:
        print("\n🎉 All tests passed! The fix should work.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Fix the issues before deploying.")
        sys.exit(1)



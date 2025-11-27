#!/usr/bin/env python3
"""
Local test script to verify Notion integration works correctly.
Tests the auth_service user lookup without Gmail connectivity.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_notion_client_basics():
    """Test 1: Verify Notion client can be created and has the right methods."""
    print("=" * 60)
    print("TEST 1: Notion Client Basics")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        if not token:
            print("❌ NOTION_TOKEN not found in environment")
            return False
        
        print(f"\n1. Creating Notion client...")
        client = Client(auth=token)
        print("   ✅ Client created")
        
        print(f"\n2. Checking available methods...")
        print(f"   - Has 'request' method: {hasattr(client, 'request')}")
        print(f"   - Has 'databases' attribute: {hasattr(client, 'databases')}")
        print(f"   - databases.query exists: {hasattr(client.databases, 'query')}")
        
        if hasattr(client, 'request'):
            import inspect
            sig = inspect.signature(client.request)
            print(f"   - request() signature: {sig}")
            params = list(sig.parameters.keys())
            print(f"   - Parameter order: {params}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notion_database_query():
    """Test 2: Test querying a Notion database using request() method."""
    print("\n" + "=" * 60)
    print("TEST 2: Notion Database Query (using request method)")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        db_id = os.getenv('NOTION_USERS_DB_ID')
        
        if not token or not db_id:
            print("❌ Missing NOTION_TOKEN or NOTION_USERS_DB_ID")
            return False
        
        print(f"\n1. Creating client and querying database: {db_id[:8]}...")
        client = Client(auth=token)
        
        # This is the exact syntax we're using in auth_service.py
        print("\n2. Testing request() method with correct syntax...")
        response = client.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                "page_size": 1  # Just get one result for testing
            }
        )
        
        print("   ✅ Query successful!")
        print(f"   - Response type: {type(response)}")
        print(f"   - Has 'results': {'results' in response}")
        print(f"   - Results count: {len(response.get('results', []))}")
        
        if response.get('results'):
            print(f"   - First result keys: {list(response['results'][0].keys())[:5]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_service_user_lookup():
    """Test 3: Test the actual auth_service.get_user_by_email() method."""
    print("\n" + "=" * 60)
    print("TEST 3: Auth Service User Lookup")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        # Use the email you're testing with
        test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
        
        print(f"\n1. Initializing AuthService...")
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        print("   ✅ AuthService initialized")
        
        print(f"\n2. Looking up user: {test_email}...")
        user = auth_service.get_user_by_email(test_email)
        
        if user:
            print(f"   ✅ User found!")
            print(f"      - Name: {user.full_name}")
            print(f"      - User ID: {user.user_id}")
            print(f"      - Task Database ID: {user.task_database_id}")
            print(f"      - Role: {user.role}")
            print(f"      - Is Active: {user.is_active}")
            
            if not user.task_database_id:
                print(f"   ⚠️  Warning: User has no task_database_id")
                return False
            
            return True
        else:
            print(f"   ❌ User not found for {test_email}")
            print(f"      ACTION: Register this email in the Notion users database")
            return False
            
    except AttributeError as e:
        if 'query' in str(e):
            print(f"\n❌ FAILED: Still trying to use databases.query()")
            print(f"   Error: {e}")
            print(f"   The fix wasn't applied correctly!")
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

def test_notion_task_insertion():
    """Test 4: Test inserting a task into Notion (if user found)."""
    print("\n" + "=" * 60)
    print("TEST 4: Notion Task Insertion (Dry Run)")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.core.notion_service import NotionService
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
        
        print(f"\n1. Getting user...")
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        user = auth_service.get_user_by_email(test_email)
        
        if not user or not user.task_database_id:
            print("   ⚠️  Skipping - user not found or no task database")
            return None  # Not a failure, just skip
        
        print(f"   ✅ User found with task database: {user.task_database_id[:8]}...")
        
        print(f"\n2. Testing task formatting...")
        notion_service = NotionService()
        
        # Create a test task
        test_task = {
            "title": "Test Task - Local Integration Test",
            "task": "This is a test task to verify Notion integration",
            "status": "Not Started",
            "employee": user.full_name,
            "date": "2025-11-01",
            "category": "Testing",
            "priority": "Medium",
            "due_date": None,
            "notes": "",
            "is_recurring": False,
            "reminder_sent": False
        }
        
        # Format task for Notion
        formatted = notion_service._format_task_properties(test_task)
        
        print(f"   ✅ Task formatted successfully")
        print(f"      Properties: {list(formatted.keys())}")
        
        # Check required fields
        required = ['Task', 'Status', 'Employee', 'Date']
        missing = [f for f in required if f not in formatted]
        
        if missing:
            print(f"   ❌ Missing required fields: {missing}")
            return False
        
        print(f"   ✅ All required fields present")
        
        # Ask if we should actually insert
        print(f"\n3. Dry run - NOT actually inserting task")
        print(f"   To test actual insertion, uncomment the code below")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "🔍" * 30)
    print("LOCAL NOTION INTEGRATION TESTS")
    print("🔍" * 30 + "\n")
    
    results = {}
    
    # Run tests
    results['client_basics'] = test_notion_client_basics()
    results['database_query'] = test_notion_database_query()
    results['user_lookup'] = test_auth_service_user_lookup()
    results['task_insertion'] = test_notion_task_insertion()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"   {status}: {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Notion integration should work.")
        print("   The issue might be elsewhere (Gmail processing, task extraction, etc.)")
    else:
        print("\n❌ Some tests failed. Fix the failing components above.")
        print("   Focus on the first failing test - that's likely the root cause.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






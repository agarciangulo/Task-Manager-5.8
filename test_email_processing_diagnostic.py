#!/usr/bin/env python3
"""
Diagnostic test script to identify issues in email processing pipeline.
Tests each step of the email → task extraction → Notion insertion flow.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_environment_setup():
    """Test 1: Verify environment variables are set."""
    print("=" * 60)
    print("TEST 1: Environment Variables")
    print("=" * 60)
    
    required_vars = {
        'GMAIL_ADDRESS': os.getenv('GMAIL_ADDRESS'),
        'GMAIL_APP_PASSWORD': os.getenv('GMAIL_APP_PASSWORD'),
        'NOTION_TOKEN': os.getenv('NOTION_TOKEN'),
        'NOTION_USERS_DB_ID': os.getenv('NOTION_USERS_DB_ID'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✅ {var_name}: {'*' * min(8, len(var_value))}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False
    
    return all_set

def test_task_extraction():
    """Test 2: Test task extraction from sample email text."""
    print("\n" + "=" * 60)
    print("TEST 2: Task Extraction")
    print("=" * 60)
    
    try:
        from src.core.task_extractor import extract_tasks_from_update
        
        sample_email = """
        Hi,
        
        Here's my update:
        - Completed the quarterly report analysis
        - Started working on the new authentication feature
        - Fixed three critical bugs in the user interface
        
        Thanks!
        """
        
        print("📧 Sample email text:")
        print(sample_email[:100] + "...")
        print("\n🔄 Extracting tasks...")
        
        tasks = extract_tasks_from_update(sample_email)
        
        print(f"\n✅ Extracted {len(tasks)} tasks")
        
        if tasks:
            print("\n📋 First task structure:")
            first_task = tasks[0]
            print(f"   Keys: {list(first_task.keys())}")
            print(f"   Sample values:")
            for key in ['task', 'status', 'employee', 'date', 'category', 'priority', 'due_date', 'notes']:
                value = first_task.get(key, 'MISSING')
                print(f"     - {key}: {value}")
            
            # Check for required fields
            required_fields = ['task', 'status', 'employee', 'date', 'category']
            missing = [f for f in required_fields if not first_task.get(f)]
            if missing:
                print(f"\n⚠️ Missing required fields: {missing}")
                return False
            else:
                print("\n✅ All required fields present")
                return True
        else:
            print("❌ No tasks extracted")
            return False
            
    except Exception as e:
        print(f"❌ Error in task extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_lookup():
    """Test 3: Test user lookup by email."""
    print("\n" + "=" * 60)
    print("TEST 3: User Lookup")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        
        test_email = os.getenv('GMAIL_ADDRESS')  # Use the Gmail address as test
        
        print(f"🔍 Looking up user for email: {test_email}")
        
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(
            os.getenv('NOTION_TOKEN'),
            os.getenv('NOTION_USERS_DB_ID'),
            jwt_manager,
            None
        )
        
        user = auth_service.get_user_by_email(test_email)
        
        if user:
            print(f"✅ User found:")
            print(f"   - User ID: {user.user_id}")
            print(f"   - Full Name: {user.full_name}")
            print(f"   - Task Database ID: {user.task_database_id}")
            
            if not user.task_database_id:
                print("❌ User does not have a task database ID")
                return False
            else:
                print("✅ User has task database configured")
                return True
        else:
            print(f"❌ User not found for email: {test_email}")
            print("   Make sure the user is registered in the Notion users database")
            return False
            
    except Exception as e:
        print(f"❌ Error in user lookup: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notion_connection():
    """Test 4: Test Notion API connection and database access."""
    print("\n" + "=" * 60)
    print("TEST 4: Notion Connection")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.core.notion_service import NotionService
        
        # Get user's database ID
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(
            os.getenv('NOTION_TOKEN'),
            os.getenv('NOTION_USERS_DB_ID'),
            jwt_manager,
            None
        )
        
        test_email = os.getenv('GMAIL_ADDRESS')
        user = auth_service.get_user_by_email(test_email)
        
        if not user or not user.task_database_id:
            print("❌ Cannot test - user not found or no database ID")
            return False
        
        print(f"🔍 Testing connection to database: {user.task_database_id}")
        
        notion_service = NotionService()
        
        # Try to fetch existing tasks
        print("🔄 Fetching existing tasks...")
        existing_tasks = notion_service.fetch_tasks(user.task_database_id)
        
        print(f"✅ Successfully connected to Notion")
        print(f"   Found {len(existing_tasks)} existing tasks in database")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Notion: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_insertion():
    """Test 5: Test inserting a task into Notion."""
    print("\n" + "=" * 60)
    print("TEST 5: Task Insertion (Dry Run)")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.core.task_extractor import extract_tasks_from_update
        from src.core.notion_service import NotionService
        
        # Get user
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(
            os.getenv('NOTION_TOKEN'),
            os.getenv('NOTION_USERS_DB_ID'),
            jwt_manager,
            None
        )
        
        test_email = os.getenv('GMAIL_ADDRESS')
        user = auth_service.get_user_by_email(test_email)
        
        if not user or not user.task_database_id:
            print("❌ Cannot test - user not found")
            return False
        
        # Extract a test task
        sample_text = "- Test task: Verify the email processing pipeline"
        tasks = extract_tasks_from_update(sample_text)
        
        if not tasks:
            print("❌ Could not extract test task")
            return False
        
        test_task = tasks[0]
        print("📋 Test task structure:")
        print(f"   {test_task}")
        
        # Format the task for Notion
        notion_service = NotionService()
        formatted_properties = notion_service._format_task_properties(test_task)
        
        print("\n📤 Formatted properties for Notion:")
        for key, value in formatted_properties.items():
            print(f"   {key}: {value}")
        
        # Check for required Notion fields
        required_notion_fields = ['Task', 'Status', 'Employee', 'Date']
        missing = [f for f in required_notion_fields if f not in formatted_properties]
        
        if missing:
            print(f"\n❌ Missing required Notion fields: {missing}")
            return False
        else:
            print("\n✅ All required Notion fields present")
            
            # Ask before actual insertion
            print("\n⚠️  DRY RUN - Not actually inserting task")
            print("   To test actual insertion, uncomment the code below")
            # Uncomment to test actual insertion:
            # success, message = notion_service.insert_task(user.task_database_id, test_task)
            # if success:
            #     print("✅ Task inserted successfully!")
            #     return True
            # else:
            #     print(f"❌ Failed to insert task: {message}")
            #     return False
            
            return True
        
    except Exception as e:
        print(f"❌ Error in task insertion test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gmail_connection():
    """Test 6: Test Gmail IMAP connection."""
    print("\n" + "=" * 60)
    print("TEST 6: Gmail Connection")
    print("=" * 60)
    
    try:
        import imaplib
        from src.config.settings import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GMAIL_SERVER
        
        print(f"🔍 Connecting to {GMAIL_SERVER}...")
        mail = imaplib.IMAP4_SSL(GMAIL_SERVER)
        
        print(f"🔐 Logging in as {GMAIL_ADDRESS}...")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        
        print("📂 Selecting INBOX...")
        status, messages = mail.select("INBOX")
        
        if status == "OK":
            print(f"✅ Successfully connected to Gmail")
            print(f"   Found {messages[0].decode()} messages in INBOX")
            
            mail.close()
            mail.logout()
            return True
        else:
            print(f"❌ Failed to select INBOX: {status}")
            mail.logout()
            return False
        
    except Exception as e:
        print(f"❌ Error connecting to Gmail: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests."""
    print("\n" + "🔍" * 30)
    print("EMAIL PROCESSING DIAGNOSTIC TESTS")
    print("🔍" * 30 + "\n")
    
    results = {}
    
    # Run all tests
    results['environment'] = test_environment_setup()
    results['task_extraction'] = test_task_extraction()
    results['user_lookup'] = test_user_lookup()
    results['notion_connection'] = test_notion_connection()
    results['task_insertion'] = test_task_insertion()
    results['gmail_connection'] = test_gmail_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Email processing should work.")
        print("   If you're still experiencing issues, check the logs for specific errors.")
    else:
        print("\n❌ Some tests failed. Fix the failing components above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






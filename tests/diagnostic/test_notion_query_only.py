#!/usr/bin/env python3
"""
Test ONLY the Notion query part - no other dependencies.
This tests if the /v1/ prefix fix works.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_notion_query():
    """Test the exact query code we're using in auth_service.py"""
    print("=" * 60)
    print("TEST: Notion Query with /v1/ prefix")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        db_id = os.getenv('NOTION_USERS_DB_ID')
        test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
        
        if not token or not db_id:
            print("❌ Missing NOTION_TOKEN or NOTION_USERS_DB_ID")
            return False
        
        print(f"\n1. Creating Notion client...")
        client = Client(auth=token)
        print("   ✅ Client created")
        
        print(f"\n2. Testing query (no /v1/ prefix - client adds it)...")
        print(f"   Path: databases/{db_id[:8]}.../query")
        print(f"   Filter: Email = {test_email}")
        
        # This is EXACTLY what auth_service.py does now
        response = client.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                "filter": {
                    "property": "Email",
                    "title": {
                        "equals": test_email
                    }
                }
            }
        )
        
        print(f"\n   ✅ Query successful!")
        print(f"   - Response type: {type(response)}")
        print(f"   - Has 'results': {'results' in response}")
        print(f"   - Results count: {len(response.get('results', []))}")
        
        if response.get('results'):
            result = response['results'][0]
            print(f"\n   ✅ User found!")
            print(f"   - Page ID: {result.get('id', 'N/A')[:8]}...")
            props = result.get('properties', {})
            
            # Extract user info
            if 'Email' in props:
                email_prop = props['Email']
                if 'title' in email_prop and email_prop['title']:
                    email_val = email_prop['title'][0].get('text', {}).get('content', 'N/A')
                    print(f"   - Email: {email_val}")
            
            if 'FullName' in props:
                name_prop = props.get('FullName', {})
                if 'rich_text' in name_prop and name_prop['rich_text']:
                    name_val = name_prop['rich_text'][0].get('text', {}).get('content', 'N/A')
                    print(f"   - Name: {name_val}")
            
            if 'TaskDatabaseID' in props:
                task_db_prop = props.get('TaskDatabaseID', {})
                if 'rich_text' in task_db_prop and task_db_prop['rich_text']:
                    task_db_val = task_db_prop['rich_text'][0].get('text', {}).get('content', 'N/A')
                    print(f"   - Task DB ID: {task_db_val[:8]}...")
            
            return True
        else:
            print(f"\n   ⚠️  No user found")
            print(f"   This email ({test_email}) is not registered in Notion")
            print(f"   Register it in the users database to proceed")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"\n   ❌ FAILED: {type(e).__name__}")
        print(f"   Error: {error_msg[:200]}")
        
        if "Invalid request URL" in error_msg:
            print(f"\n   🚨 Still getting 'Invalid request URL'")
            print(f"   The /v1/ prefix might not be enough")
            print(f"   Or there's another issue with the path format")
        elif "query" in error_msg and "attribute" in error_msg:
            print(f"\n   🚨 Still trying to use databases.query()")
            print(f"   The fix wasn't applied correctly")
        
        import traceback
        print(f"\n   Full traceback:")
        traceback.print_exc()
        return False

def test_simple_query():
    """Test a simple query without filters to verify connection works"""
    print("\n" + "=" * 60)
    print("TEST: Simple Query (no filters)")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        db_id = os.getenv('NOTION_USERS_DB_ID')
        
        client = Client(auth=token)
        
        print(f"\n1. Testing simple query (get 1 result)...")
        response = client.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={"page_size": 1}
        )
        
        print(f"   ✅ Query successful!")
        print(f"   - Results: {len(response.get('results', []))}")
        
        if response.get('results'):
            print(f"   - First result ID: {response['results'][0].get('id', 'N/A')[:8]}...")
            return True
        else:
            print(f"   - Database is empty (no users registered)")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Notion Query (No Dependencies)\n")
    
    test1 = test_simple_query()
    test2 = test_notion_query()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Simple Query: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"User Lookup Query: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n✅ All tests passed! The fix works correctly.")
        print("   Safe to deploy.")
    elif test1 and not test2:
        print("\n⚠️  Connection works but user not found.")
        print("   Register the test email in Notion users database.")
    else:
        print("\n❌ Query is failing. Check the error above.")
    
    sys.exit(0 if (test1 and test2) else 1)


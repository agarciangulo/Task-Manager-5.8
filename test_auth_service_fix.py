#!/usr/bin/env python3
"""
Test the exact auth_service code that's deployed - isolate the Notion query issue.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_notion_query_exact():
    """Test the exact query code we're using in auth_service.py"""
    print("=" * 60)
    print("TESTING EXACT AUTH_SERVICE CODE")
    print("=" * 60)
    
    try:
        from notion_client import Client
        
        token = os.getenv('NOTION_TOKEN')
        db_id = os.getenv('NOTION_USERS_DB_ID')
        test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
        
        if not token or not db_id:
            print("❌ Missing environment variables")
            return False
        
        print(f"\n1. Creating Notion client...")
        client = Client(auth=token)
        print("   ✅ Client created")
        
        print(f"\n2. Testing EXACT code from auth_service.py...")
        print(f"   Path: databases/{db_id}/query")
        print(f"   Method: POST")
        print(f"   Filter: Email equals {test_email}")
        
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
        print(f"   - Has results: {'results' in response}")
        print(f"   - Results count: {len(response.get('results', []))}")
        
        if response.get('results'):
            result = response['results'][0]
            print(f"   - Found user page!")
            print(f"   - Page ID: {result.get('id', 'N/A')[:8]}...")
            props = result.get('properties', {})
            if 'Email' in props:
                email_prop = props['Email']
                if 'title' in email_prop and email_prop['title']:
                    email_val = email_prop['title'][0].get('text', {}).get('content', 'N/A')
                    print(f"   - Email from result: {email_val}")
            
            return True
        else:
            print(f"   ⚠️  No user found with email: {test_email}")
            print(f"   This means the user isn't registered in Notion")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"   Error: {str(e)[:200]}")
        
        # Check if it's the query attribute error
        if 'query' in str(e) and 'attribute' in str(e):
            print(f"\n   🚨 This is the SAME error from production!")
            print(f"   The fix didn't work - request() method also failing")
        
        import traceback
        print(f"\n   Full traceback:")
        traceback.print_exc()
        return False

def test_what_works_in_notion_service():
    """Test what notion_service.py does - does it actually work?"""
    print("\n" + "=" * 60)
    print("TESTING WHAT notion_service.py DOES")
    print("=" * 60)
    
    try:
        from src.core.notion_service import NotionService
        from src.config.settings import NOTION_USERS_DB_ID
        
        print(f"\n1. Creating NotionService...")
        service = NotionService()
        print("   ✅ Service created")
        
        print(f"\n2. Testing fetch_tasks() - this uses databases.query()...")
        # This should fail if databases.query() doesn't exist
        tasks = service.fetch_tasks(NOTION_USERS_DB_ID, days_back=7)
        
        print(f"   ✅ fetch_tasks() worked!")
        print(f"   - Tasks returned: {len(tasks)}")
        print(f"   - This means databases.query() DOES work somehow!")
        
        return True
        
    except AttributeError as e:
        if 'query' in str(e):
            print(f"   ❌ databases.query() doesn't exist - notion_service.py is also broken!")
            return False
        else:
            print(f"   ❌ Error: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Notion Integration - Exact Production Code\n")
    
    test1 = test_notion_query_exact()
    test2 = test_what_works_in_notion_service()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    
    if test1:
        print("✅ auth_service query works! The fix is correct.")
        print("   If it still fails in production, check deployment.")
    elif test2:
        print("⚠️  notion_service.query() works but auth_service doesn't")
        print("   Check the difference between the two implementations")
    else:
        print("❌ Both methods failing")
        print("   Check Notion API token and database ID")



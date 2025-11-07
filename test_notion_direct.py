#!/usr/bin/env python3
"""
Direct test of Notion API to find the correct path format.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_direct_api():
    """Test the Notion API directly with requests to see what works."""
    print("=" * 60)
    print("TESTING NOTION API DIRECTLY")
    print("=" * 60)
    
    import requests
    
    token = os.getenv('NOTION_TOKEN')
    db_id = os.getenv('NOTION_USERS_DB_ID')
    
    if not token or not db_id:
        print("❌ Missing NOTION_TOKEN or NOTION_USERS_DB_ID")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Test different URL formats
    base_url = "https://api.notion.com/v1"
    
    print(f"\n1. Testing direct API call with correct URL...")
    url = f"{base_url}/databases/{db_id}/query"
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json={"page_size": 1}
        )
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! Direct API call works")
            data = response.json()
            print(f"   - Results: {len(data.get('results', []))}")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   - Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_notion_client_request():
    """Test what the notion-client request method actually does."""
    print("\n" + "=" * 60)
    print("TESTING NOTION CLIENT REQUEST METHOD")
    print("=" * 60)
    
    from notion_client import Client
    
    token = os.getenv('NOTION_TOKEN')
    db_id = os.getenv('NOTION_USERS_DB_ID')
    
    client = Client(auth=token)
    
    # The client might automatically add /v1/, so try without it
    print(f"\n1. Testing with path WITHOUT /v1/ prefix...")
    try:
        response = client.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={"page_size": 1}
        )
        print(f"   ✅ SUCCESS without /v1/!")
        print(f"   - Results: {len(response.get('results', []))}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {type(e).__name__}: {str(e)[:100]}")
    
    # Try with /v1/
    print(f"\n2. Testing with path WITH /v1/ prefix...")
    try:
        response = client.request(
            path=f"/v1/databases/{db_id}/query",
            method="POST",
            body={"page_size": 1}
        )
        print(f"   ✅ SUCCESS with /v1/!")
        print(f"   - Results: {len(response.get('results', []))}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {type(e).__name__}: {str(e)[:100]}")
    
    return False

def test_auth_service_method():
    """Test what the actual auth_service code does."""
    print("\n" + "=" * 60)
    print("TESTING AUTH SERVICE CODE (if dependencies available)")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
        
        print(f"\n1. Initializing AuthService...")
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        
        print(f"\n2. Looking up user: {test_email}...")
        user = auth_service.get_user_by_email(test_email)
        
        if user:
            print(f"   ✅ User found: {user.full_name}")
            return True
        else:
            print(f"   ❌ User not found")
            return False
            
    except ImportError as e:
        print(f"   ⚠️  Can't test - missing dependency: {e}")
        print(f"   This is expected if bcrypt isn't installed locally")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Notion API Integration\n")
    
    test1 = test_direct_api()
    test2 = test_notion_client_request()
    test3 = test_auth_service_method()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Direct API: {'✅' if test1 else '❌'}")
    print(f"Client Request: {'✅' if test2 else '❌'}")
    print(f"Auth Service: {'✅' if test3 else '❌' if test3 is False else '⏭️'}")
    
    if test1 and test2:
        print("\n✅ API works! The issue is likely in how we're calling it.")
    elif test1 and not test2:
        print("\n⚠️  Direct API works but client.request() doesn't - check path format")
    else:
        print("\n❌ API itself might be failing - check token and database ID")



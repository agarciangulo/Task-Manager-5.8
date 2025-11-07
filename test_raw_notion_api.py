#!/usr/bin/env python3
"""
Test using raw HTTP requests to Notion API - bypassing the client.
This would work with any notion-client version.
"""
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_raw_notion_query():
    """Test querying Notion using raw HTTP requests."""
    print("=" * 60)
    print("TEST: Raw Notion API (bypassing client)")
    print("=" * 60)
    
    token = os.getenv('NOTION_TOKEN')
    db_id = os.getenv('NOTION_USERS_DB_ID')
    test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
    
    if not token or not db_id:
        print("❌ Missing env vars")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    
    print(f"\n1. Testing direct Notion API call...")
    print(f"   URL: {url}")
    print(f"   Method: POST")
    
    try:
        response = httpx.post(
            url,
            headers=headers,
            json={
                "filter": {
                    "property": "Email",
                    "title": {
                        "equals": test_email
                    }
                }
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   ✅ SUCCESS!")
            print(f"   - Results: {len(data.get('results', []))}")
            
            if data.get('results'):
                result = data['results'][0]
                print(f"   - User found!")
                props = result.get('properties', {})
                if 'Email' in props:
                    email_val = props['Email'].get('title', [{}])[0].get('text', {}).get('content', 'N/A')
                    print(f"   - Email: {email_val}")
                return True
            else:
                print(f"   - User not found (register {test_email})")
                return False
        else:
            print(f"\n   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Raw Notion API\n")
    
    success = test_raw_notion_query()
    
    if success:
        print("\n✅ Raw API works! We can use this as a fallback.")
        print("   Or upgrade notion-client to 2.x which has databases.query()")
    else:
        print("\n❌ Raw API also failed. Check token and database ID.")
    
    sys.exit(0 if success else 1)



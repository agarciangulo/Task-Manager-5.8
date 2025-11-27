#!/usr/bin/env python3
"""
Simple test to verify the Notion query fix syntax is correct.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_query_syntax():
    """Test the query syntax we're using."""
    print("=" * 60)
    print("TESTING NOTION QUERY SYNTAX")
    print("=" * 60)
    
    try:
        from notion_client import Client
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        print("\n1. Creating Notion client...")
        client = Client(auth=NOTION_TOKEN)
        print("   ✅ Client created")
        
        print(f"\n2. Testing query with database: {NOTION_USERS_DB_ID[:8]}...")
        
        # This is the exact syntax we're using in auth_service.py
        response = client.request(
            path=f"databases/{NOTION_USERS_DB_ID}/query",
            method="POST",
            body={
                "filter": {
                    "property": "Email",
                    "title": {
                        "equals": "test@example.com"
                    }
                }
            }
        )
        
        print(f"   ✅ Query successful!")
        print(f"      Response type: {type(response)}")
        print(f"      Has 'results': {'results' in response}")
        print(f"      Results count: {len(response.get('results', []))}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Notion Query Syntax\n")
    
    success = test_query_syntax()
    
    if success:
        print("\n🎉 Test passed! The syntax is correct and should work in production.")
        sys.exit(0)
    else:
        print("\n❌ Test failed. Check the error above.")
        sys.exit(1)






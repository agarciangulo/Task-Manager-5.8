#!/usr/bin/env python3
"""
Simple Notion page access test with different approaches.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def test_page_access():
    """Test page access with different approaches."""
    print("🔍 Simple Notion Page Access Test")
    print("=" * 40)
    
    notion_token = os.getenv('NOTION_TOKEN')
    page_id = os.getenv('NOTION_PARENT_PAGE_ID')
    
    print(f"Token: {'✅ Found' if notion_token else '❌ Missing'}")
    print(f"Page ID: {page_id}")
    
    if not notion_token or not page_id:
        print("❌ Missing required environment variables")
        return
    
    try:
        client = Client(auth=notion_token)
        
        # Test 1: Try with different page ID formats
        print(f"\n1. Testing different page ID formats...")
        
        # Original format
        try:
            page = client.pages.retrieve(page_id=page_id)
            print(f"   ✅ Original format works!")
            print(f"   Page title: {page.get('properties', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}")
            return True
        except Exception as e:
            print(f"   ❌ Original format failed: {str(e)}")
        
        # With dashes
        try:
            formatted_id = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
            page = client.pages.retrieve(page_id=formatted_id)
            print(f"   ✅ Dashed format works!")
            print(f"   Page title: {page.get('properties', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}")
            return True
        except Exception as e:
            print(f"   ❌ Dashed format failed: {str(e)}")
        
        # Test 2: Try to search for the page
        print(f"\n2. Searching for pages...")
        try:
            search_results = client.search(query="", filter={"property": "object", "value": "page"})
            print(f"   Found {len(search_results.get('results', []))} pages")
            
            for i, result in enumerate(search_results.get('results', [])[:5]):
                result_id = result.get('id', '')
                title = result.get('properties', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
                print(f"   {i+1}. {title} (ID: {result_id})")
                
                if result_id.replace('-', '') == page_id:
                    print(f"   🎯 Found matching page!")
                    return True
                    
        except Exception as e:
            print(f"   ❌ Search failed: {str(e)}")
        
        # Test 3: Try to list databases
        print(f"\n3. Listing databases...")
        try:
            databases = client.search(query="", filter={"property": "object", "value": "database"})
            print(f"   Found {len(databases.get('results', []))} databases")
            
            for i, db in enumerate(databases.get('results', [])[:3]):
                title = db.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
                print(f"   {i+1}. {title}")
                
        except Exception as e:
            print(f"   ❌ Database list failed: {str(e)}")
        
        print(f"\n❌ Could not access the specified page")
        print(f"💡 The page ID might be incorrect or the page doesn't exist")
        print(f"💡 Make sure you've created a page and shared it with your 'Follow Ups' integration")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_page_access() 
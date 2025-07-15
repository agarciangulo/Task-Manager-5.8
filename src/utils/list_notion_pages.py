#!/usr/bin/env python3
"""
Script to list all available Notion pages and find the correct parent page ID.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def list_available_pages():
    """List all available pages in Notion."""
    print("🔍 Listing Available Notion Pages")
    print("=" * 50)
    
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print("❌ NOTION_TOKEN not found")
        return
    
    try:
        client = Client(auth=notion_token)
        
        # Get all pages
        print("📄 Available Pages:")
        print("-" * 30)
        
        search_results = client.search(query="", filter={"property": "object", "value": "page"})
        pages = search_results.get('results', [])
        
        if not pages:
            print("❌ No pages found")
            return
        
        print(f"Found {len(pages)} pages:")
        print()
        
        for i, page in enumerate(pages[:20]):  # Show first 20 pages
            page_id = page.get('id', '')
            page_id_clean = page_id.replace('-', '')
            
            # Try to get the title
            title = "Untitled"
            try:
                title_prop = page.get('properties', {}).get('title', [])
                if title_prop:
                    title = title_prop[0].get('text', {}).get('content', 'Untitled')
            except:
                pass
            
            print(f"{i+1:2d}. {title}")
            print(f"     ID: {page_id}")
            print(f"     Clean ID: {page_id_clean}")
            print()
        
        if len(pages) > 20:
            print(f"... and {len(pages) - 20} more pages")
        
        print("\n📋 Instructions:")
        print("1. Look for a page you want to use as the parent page")
        print("2. Copy the 'Clean ID' (the one without dashes)")
        print("3. Update your .env file with: NOTION_PARENT_PAGE_ID=clean-id-here")
        print("4. Make sure that page is shared with your 'Follow Ups' integration")
        
        # Check if current page ID exists
        current_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
        if current_page_id:
            print(f"\n🔍 Checking current page ID: {current_page_id}")
            found = False
            for page in pages:
                if page.get('id', '').replace('-', '') == current_page_id:
                    print(f"✅ Found! Page: {page.get('properties', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}")
                    found = True
                    break
            
            if not found:
                print(f"❌ Current page ID not found in available pages")
                print(f"💡 You need to either:")
                print(f"   - Create a new page and share it with your integration")
                print(f"   - Use one of the existing pages above")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    list_available_pages() 
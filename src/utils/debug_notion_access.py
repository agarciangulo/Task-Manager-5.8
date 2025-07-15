#!/usr/bin/env python3
"""
Detailed diagnostic script for Notion page access issues.
"""

import os
import re
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def validate_page_id(page_id):
    """Validate the format of a Notion page ID."""
    print(f"🔍 Validating page ID format...")
    print(f"   Page ID: {page_id}")
    print(f"   Length: {len(page_id)} characters")
    
    # Notion page IDs are typically 32 characters long
    if len(page_id) != 32:
        print(f"   ⚠️ Warning: Expected 32 characters, got {len(page_id)}")
    
    # Check if it contains only valid characters (hex)
    if not re.match(r'^[a-f0-9]+$', page_id):
        print(f"   ❌ Error: Page ID contains invalid characters")
        print(f"   Page ID should only contain lowercase letters a-f and numbers 0-9")
        return False
    
    print(f"   ✅ Page ID format looks valid")
    return True

def test_notion_connection():
    """Test basic Notion connection."""
    print(f"\n🔍 Testing basic Notion connection...")
    
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print(f"   ❌ NOTION_TOKEN not found")
        return False
    
    try:
        client = Client(auth=notion_token)
        
        # Test basic API access
        integration = client.users.me()
        print(f"   ✅ Notion connection successful")
        print(f"   ✅ Integration: {integration.get('name', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"   ❌ Notion connection failed: {str(e)}")
        return False

def test_page_access(page_id):
    """Test access to a specific page."""
    print(f"\n🔍 Testing page access...")
    
    notion_token = os.getenv('NOTION_TOKEN')
    client = Client(auth=notion_token)
    
    try:
        # Try to retrieve the page
        page = client.pages.retrieve(page_id=page_id)
        print(f"   ✅ Page access successful!")
        print(f"   ✅ Page title: {page.get('properties', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}")
        return True
        
    except Exception as e:
        print(f"   ❌ Page access failed: {str(e)}")
        
        # Provide specific guidance based on error
        if "not_found" in str(e).lower():
            print(f"   💡 The page doesn't exist or the ID is incorrect")
        elif "unauthorized" in str(e).lower() or "forbidden" in str(e).lower():
            print(f"   💡 Your integration doesn't have access to this page")
            print(f"   💡 Make sure to share the page with your 'Follow Ups' integration")
        else:
            print(f"   💡 Unknown error - check the page ID and permissions")
        
        return False

def show_detailed_instructions():
    """Show detailed setup instructions."""
    print(f"\n📖 Detailed Setup Instructions")
    print(f"=" * 50)
    print(f"1. Create a new page in Notion:")
    print(f"   - Go to https://notion.so")
    print(f"   - Click 'Add a page'")
    print(f"   - Give it a name like 'Task Databases'")
    
    print(f"\n2. Share the page with your integration:")
    print(f"   - Click 'Share' in the top right corner")
    print(f"   - Click 'Invite'")
    print(f"   - In the search box, type: Follow Ups")
    print(f"   - Select 'Follow Ups' from the results")
    print(f"   - Make sure it has 'Edit' permissions")
    print(f"   - Click 'Invite'")
    
    print(f"\n3. Get the page ID:")
    print(f"   - Look at the URL in your browser")
    print(f"   - It should look like: https://notion.so/Task-Databases-{'{32-char-id}'}")
    print(f"   - Copy the 32-character ID at the end")
    print(f"   - Example: If URL ends with -2175c6ec3b8080d183d0c0e4fb219f9d")
    print(f"   - Then the ID is: 2175c6ec3b8080d183d0c0e4fb219f9d")
    
    print(f"\n4. Update your .env file:")
    print(f"   - Open your .env file")
    print(f"   - Find the line: NOTION_PARENT_PAGE_ID=...")
    print(f"   - Replace the value with your new page ID")
    print(f"   - Save the file")
    
    print(f"\n5. Test again:")
    print(f"   - Run: python test_notion_parent_page.py")

def main():
    """Run the diagnostic."""
    print("🔧 Notion Page Access Diagnostic")
    print("=" * 50)
    
    # Get the page ID
    page_id = os.getenv('NOTION_PARENT_PAGE_ID')
    if not page_id:
        print("❌ NOTION_PARENT_PAGE_ID not found in .env file")
        show_detailed_instructions()
        return
    
    # Validate page ID format
    if not validate_page_id(page_id):
        print("\n❌ Page ID format is invalid")
        show_detailed_instructions()
        return
    
    # Test Notion connection
    if not test_notion_connection():
        print("\n❌ Cannot connect to Notion")
        return
    
    # Test page access
    if not test_page_access(page_id):
        print("\n❌ Cannot access the specified page")
        show_detailed_instructions()
        return
    
    print(f"\n🎉 All tests passed! Your page is properly configured.")

if __name__ == "__main__":
    main() 
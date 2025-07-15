#!/usr/bin/env python3
"""
Test script to verify Notion parent page connection and permissions.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def test_notion_parent_page():
    """Test Notion parent page connection and permissions."""
    print("🔍 Testing Notion Parent Page Connection")
    print("=" * 50)
    
    # Get environment variables
    notion_token = os.getenv('NOTION_TOKEN')
    parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
    
    print(f"NOTION_TOKEN: {'✅ Found' if notion_token else '❌ Missing'}")
    print(f"NOTION_PARENT_PAGE_ID: {'✅ Found' if parent_page_id else '❌ Missing'}")
    
    if not notion_token:
        print("\n❌ NOTION_TOKEN is required. Please add it to your .env file.")
        return False
    
    if not parent_page_id:
        print("\n❌ NOTION_PARENT_PAGE_ID is required. Please add it to your .env file.")
        print("This should be the ID of a Notion page where user task databases will be created.")
        return False
    
    try:
        # Initialize Notion client
        client = Client(auth=notion_token)
        
        # Test 1: Try to retrieve the parent page
        print(f"\n1. Testing parent page access...")
        print(f"   Parent Page ID: {parent_page_id}")
        
        try:
            parent_page = client.pages.retrieve(page_id=parent_page_id)
            print(f"   ✅ Parent page found: {parent_page.get('properties', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}")
        except Exception as e:
            print(f"   ❌ Failed to access parent page: {str(e)}")
            print("   This could mean:")
            print("   - The page ID is incorrect")
            print("   - Your integration doesn't have access to this page")
            print("   - The page doesn't exist")
            return False
        
        # Test 2: Check if we can create a database (test creation)
        print(f"\n2. Testing database creation permissions...")
        
        try:
            # Try to create a test database
            test_database = client.databases.create(
                parent={"page_id": parent_page_id},
                title=[
                    {
                        "type": "text",
                        "text": {
                            "content": "Test Database - Will be deleted"
                        }
                    }
                ],
                properties={
                    "Name": {
                        "title": {}
                    }
                }
            )
            
            test_db_id = test_database["id"]
            print(f"   ✅ Successfully created test database: {test_db_id}")
            
            # Clean up: Delete the test database
            print(f"   🧹 Cleaning up test database...")
            client.pages.update(page_id=test_db_id, archived=True)
            print(f"   ✅ Test database deleted")
            
        except Exception as e:
            print(f"   ❌ Failed to create database: {str(e)}")
            print("   This means your integration doesn't have permission to create databases in this page.")
            print("   Please ensure:")
            print("   - The page is shared with your integration")
            print("   - Your integration has 'Edit' permissions")
            return False
        
        # Test 3: Check integration capabilities
        print(f"\n3. Testing integration capabilities...")
        
        try:
            # Get integration info
            integration = client.users.me()
            print(f"   ✅ Integration name: {integration.get('name', 'Unknown')}")
            print(f"   ✅ Integration type: {integration.get('type', 'Unknown')}")
            
        except Exception as e:
            print(f"   ⚠️ Could not get integration info: {str(e)}")
        
        print(f"\n🎉 All tests passed! Your Notion parent page is properly configured.")
        print(f"\n📋 Summary:")
        print(f"   - Parent page access: ✅ Working")
        print(f"   - Database creation: ✅ Working")
        print(f"   - Integration permissions: ✅ Sufficient")
        print(f"\n🚀 Ready to test user-specific task databases!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

def show_setup_instructions():
    """Show setup instructions for the parent page."""
    print("\n📖 Setup Instructions for NOTION_PARENT_PAGE_ID")
    print("=" * 60)
    print("1. Create a new page in Notion (or use an existing one)")
    print("2. Share this page with your Notion integration:")
    print("   - Click 'Share' in the top right")
    print("   - Click 'Invite'")
    print("   - Search for your integration name")
    print("   - Select it and give it 'Edit' permissions")
    print("3. Copy the page ID from the URL:")
    print("   - URL format: https://notion.so/Your-Page-Name-{page-id}")
    print("   - Copy the {page-id} part (32 characters)")
    print("4. Add to your .env file:")
    print("   NOTION_PARENT_PAGE_ID=your-page-id-here")
    print("\nExample .env entry:")
    print("NOTION_PARENT_PAGE_ID=1e35c6ec-8f4a-4b2c-9d3e-5f6a7b8c9d0e")

def main():
    """Run the parent page test."""
    print("🚀 Notion Parent Page Connection Test")
    print("=" * 60)
    
    success = test_notion_parent_page()
    
    if not success:
        print("\n❌ Parent page test failed.")
        show_setup_instructions()
    else:
        print("\n✅ Ready to test the user-specific task system!")
        print("You can now run: python test_user_tasks.py")
    
    return success

if __name__ == "__main__":
    main() 
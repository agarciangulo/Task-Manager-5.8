#!/usr/bin/env python3
"""
Script to find the Notion integration name.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def find_integration():
    """Find the Notion integration name."""
    print("🔍 Finding Notion Integration Name")
    print("=" * 40)
    
    notion_token = os.getenv('NOTION_TOKEN')
    
    if not notion_token:
        print("❌ NOTION_TOKEN not found in .env file")
        return
    
    try:
        client = Client(auth=notion_token)
        integration = client.users.me()
        
        print(f"✅ Integration Name: {integration.get('name', 'Unknown')}")
        print(f"✅ Integration Type: {integration.get('type', 'Unknown')}")
        print(f"✅ Integration ID: {integration.get('id', 'Unknown')}")
        
        print(f"\n📋 Next Steps:")
        print(f"1. Go to Notion and create a new page (or use an existing one)")
        print(f"2. Click 'Share' in the top right corner")
        print(f"3. Click 'Invite'")
        print(f"4. Search for: {integration.get('name', 'Your Integration')}")
        print(f"5. Select it and give it 'Edit' permissions")
        print(f"6. Copy the page ID from the URL and update your .env file")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    find_integration() 
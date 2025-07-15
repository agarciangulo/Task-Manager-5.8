#!/usr/bin/env python3
"""
Script to help find and verify task databases in Notion.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_EMAIL = "test_user_20250620_074505@example.com"  # From the successful test
TEST_PASSWORD = "testpassword123"

def find_task_database():
    """Find and display information about the user's task database."""
    print("🔍 Finding Task Database in Notion")
    print("=" * 50)
    
    # Step 1: Login to get user info
    print(f"1. Logging in as {TEST_EMAIL}...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return
    
    token = response.json().get("token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Login successful")
    
    # Step 2: Get user profile
    print(f"\n2. Getting user profile...")
    response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get profile: {response.status_code} - {response.text}")
        return
    
    profile = response.json().get("user", {})
    task_database_id = profile.get("task_database_id")
    user_name = profile.get("full_name")
    
    if not task_database_id:
        print("❌ No task database found for this user")
        return
    
    print(f"✅ Found task database!")
    print(f"\n📋 Database Information:")
    print(f"   User: {user_name}")
    print(f"   Database ID: {task_database_id}")
    print(f"   Database Name: Tasks - {user_name}")
    
    print(f"\n🔗 Direct Links:")
    print(f"   Notion URL: https://notion.so/{task_database_id}")
    print(f"   Parent Page ID: {os.getenv('NOTION_PARENT_PAGE_ID')}")
    
    print(f"\n📝 How to Find in Notion:")
    print(f"   1. Go to your Notion workspace")
    print(f"   2. Navigate to the parent page (ID: {os.getenv('NOTION_PARENT_PAGE_ID')})")
    print(f"   3. Look for database: 'Tasks - {user_name}'")
    print(f"   4. Or use the direct URL above")
    
    print(f"\n🎯 Database Structure:")
    print(f"   - Task (Title): Task description")
    print(f"   - Status (Select): Not Started, In Progress, Completed, On Hold")
    print(f"   - Priority (Select): Low, Medium, High, Urgent")
    print(f"   - Category (Text): Task category/project")
    print(f"   - Due Date (Date): When the task is due")
    print(f"   - Created (Date): When the task was created")
    print(f"   - Notes (Text): Additional notes")
    print(f"   - Assigned To (Text): Who the task is assigned to")

if __name__ == "__main__":
    find_task_database() 
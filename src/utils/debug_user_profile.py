#!/usr/bin/env python3
"""
Debug script to check user profile in Notion and verify task database ID.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_EMAIL = "test_user_20250620_074319@example.com"  # From the last test
TEST_PASSWORD = "testpassword123"

def debug_user_profile():
    """Debug the user profile to see what's stored in Notion."""
    print("🔍 Debugging User Profile")
    print("=" * 40)
    
    # Step 1: Login to get token
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
    
    # Step 2: Get user profile via API
    print(f"\n2. Getting user profile via API...")
    response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get profile: {response.status_code} - {response.text}")
        return
    
    profile = response.json().get("user", {})
    print("📋 User Profile from API:")
    print(f"   User ID: {profile.get('user_id')}")
    print(f"   Email: {profile.get('email')}")
    print(f"   Full Name: {profile.get('full_name')}")
    print(f"   Task Database ID: {profile.get('task_database_id', 'None')}")
    print(f"   Role: {profile.get('role')}")
    print(f"   Is Active: {profile.get('is_active')}")
    
    # Step 3: Check if task database exists
    task_db_id = profile.get('task_database_id')
    if task_db_id:
        print(f"\n3. Task database ID found: {task_db_id}")
        print("✅ Task database was created and saved to user profile!")
    else:
        print(f"\n3. No task database ID found in profile")
        print("❌ Task database was not saved to user profile")
        
        # Check if we can manually create the task database
        print(f"\n4. Trying to manually create task database...")
        parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
        if parent_page_id:
            response = requests.post(f"{BASE_URL}/api/user/task-database", 
                                   json={"parent_page_id": parent_page_id}, 
                                   headers=headers)
            
            if response.status_code == 201:
                database_id = response.json().get("database_id")
                print(f"✅ Manual task database creation successful: {database_id}")
                
                # Check profile again
                response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
                if response.status_code == 200:
                    profile = response.json().get("user", {})
                    new_task_db_id = profile.get('task_database_id')
                    if new_task_db_id:
                        print(f"✅ Profile now shows task database: {new_task_db_id}")
                    else:
                        print("❌ Profile still doesn't show task database")
            else:
                print(f"❌ Manual task database creation failed: {response.status_code} - {response.text}")
        else:
            print("❌ NOTION_PARENT_PAGE_ID not set")

if __name__ == "__main__":
    debug_user_profile() 
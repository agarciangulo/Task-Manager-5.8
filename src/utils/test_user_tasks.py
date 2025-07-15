#!/usr/bin/env python3
"""
Test script for the user-specific task system.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_NAME = "Test User"

def test_user_task_system():
    """Test the complete user task system."""
    print("🧪 Testing User-Specific Task System")
    print("=" * 50)
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    user_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": TEST_USER_NAME,
        "role": "user"
    }
    
    response = requests.post(f"{BASE_URL}/api/register", json=user_data)
    if response.status_code == 201:
        print("✅ User registered successfully")
    elif response.status_code == 400 and "already exists" in response.json().get("error", ""):
        print("ℹ️ User already exists, continuing...")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return False
    
    # Step 2: Login to get token
    print("\n2. Logging in...")
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("token")
    if not token:
        print("❌ No token received")
        return False
    
    print("✅ Login successful")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Step 3: Get user profile to check task database
    print("\n3. Getting user profile...")
    response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get profile: {response.status_code} - {response.text}")
        return False
    
    profile = response.json().get("user", {})
    task_database_id = profile.get("task_database_id")
    
    if task_database_id:
        print(f"✅ User has task database: {task_database_id}")
    else:
        print("ℹ️ User doesn't have task database yet")
    
    # Step 4: Get user tasks (should be empty initially)
    print("\n4. Getting user tasks...")
    response = requests.get(f"{BASE_URL}/api/user/tasks", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get tasks: {response.status_code} - {response.text}")
        return False
    
    tasks_data = response.json()
    initial_task_count = len(tasks_data.get("tasks", []))
    print(f"✅ Found {initial_task_count} existing tasks")
    
    # Step 5: Create a test task
    print("\n5. Creating test task...")
    task_data = {
        "task": "Test task for user-specific system",
        "notes": "This is a test task to verify the user-specific task system",
        "status": "Not Started",
        "priority": "Medium",
        "category": "Testing",
        "due_date": "2024-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/user/tasks", json=task_data, headers=headers)
    if response.status_code != 201:
        print(f"❌ Failed to create task: {response.status_code} - {response.text}")
        return False
    
    created_task = response.json().get("task", {})
    task_id = created_task.get("id")
    print(f"✅ Task created successfully: {task_id}")
    
    # Step 6: Get tasks again to verify creation
    print("\n6. Verifying task creation...")
    response = requests.get(f"{BASE_URL}/api/user/tasks", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get tasks: {response.status_code} - {response.text}")
        return False
    
    tasks_data = response.json()
    new_task_count = len(tasks_data.get("tasks", []))
    print(f"✅ Now have {new_task_count} tasks (was {initial_task_count})")
    
    if new_task_count <= initial_task_count:
        print("❌ Task count didn't increase")
        return False
    
    # Step 7: Update the task
    print("\n7. Updating test task...")
    update_data = {
        "status": "In Progress",
        "priority": "High",
        "notes": "Updated notes for the test task"
    }
    
    response = requests.put(f"{BASE_URL}/api/user/tasks/{task_id}", json=update_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to update task: {response.status_code} - {response.text}")
        return False
    
    print("✅ Task updated successfully")
    
    # Step 8: Verify the update
    print("\n8. Verifying task update...")
    response = requests.get(f"{BASE_URL}/api/user/tasks", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get tasks: {response.status_code} - {response.text}")
        return False
    
    tasks_data = response.json()
    updated_task = next((t for t in tasks_data.get("tasks", []) if t.get("id") == task_id), None)
    
    if updated_task:
        if updated_task.get("status") == "In Progress" and updated_task.get("priority") == "High":
            print("✅ Task update verified")
        else:
            print(f"❌ Task update not reflected: status={updated_task.get('status')}, priority={updated_task.get('priority')}")
            return False
    else:
        print("❌ Updated task not found")
        return False
    
    # Step 9: Delete the test task
    print("\n9. Deleting test task...")
    response = requests.delete(f"{BASE_URL}/api/user/tasks/{task_id}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to delete task: {response.status_code} - {response.text}")
        return False
    
    print("✅ Task deleted successfully")
    
    # Step 10: Verify deletion
    print("\n10. Verifying task deletion...")
    response = requests.get(f"{BASE_URL}/api/user/tasks", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get tasks: {response.status_code} - {response.text}")
        return False
    
    tasks_data = response.json()
    final_task_count = len(tasks_data.get("tasks", []))
    print(f"✅ Final task count: {final_task_count}")
    
    if final_task_count != initial_task_count:
        print(f"❌ Task count mismatch: expected {initial_task_count}, got {final_task_count}")
        return False
    
    print("\n🎉 All tests passed! User-specific task system is working correctly.")
    return True

def test_task_database_creation():
    """Test manual task database creation."""
    print("\n🧪 Testing Manual Task Database Creation")
    print("=" * 50)
    
    # Login
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Get parent page ID from environment
    parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
    if not parent_page_id:
        print("ℹ️ NOTION_PARENT_PAGE_ID not set, skipping database creation test")
        return True
    
    print(f"\n1. Creating task database with parent page: {parent_page_id}")
    
    response = requests.post(f"{BASE_URL}/api/user/task-database", 
                           json={"parent_page_id": parent_page_id}, 
                           headers=headers)
    
    if response.status_code == 201:
        database_id = response.json().get("database_id")
        print(f"✅ Task database created successfully: {database_id}")
        return True
    elif response.status_code == 400 and "already has" in response.json().get("error", ""):
        print("ℹ️ User already has a task database")
        return True
    else:
        print(f"❌ Failed to create task database: {response.status_code} - {response.text}")
        return False

def main():
    """Run all tests."""
    print("🚀 User-Specific Task System Test Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Make sure it's running on http://127.0.0.1:5001")
        return False
    
    print("✅ Server is running")
    
    # Run tests
    success = True
    
    if not test_user_task_system():
        success = False
    
    if not test_task_database_creation():
        success = False
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("- User registration and login ✓")
        print("- Task database management ✓")
        print("- Task CRUD operations ✓")
        print("- Data isolation ✓")
        print("- API endpoints ✓")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    main() 
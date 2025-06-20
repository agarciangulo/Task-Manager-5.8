#!/usr/bin/env python3
"""
Test script to create a new user and verify the task database schema.
This will help us confirm that the updated UserTaskService creates the correct properties.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import NOTION_TOKEN, NOTION_USERS_DB_ID, NOTION_PARENT_PAGE_ID
from core.services.auth_service import AuthService
from core.security.jwt_utils import JWTManager
from notion_client import Client

def test_new_user_creation():
    """Test creating a new user and checking their task database schema."""
    
    print("🧪 Testing New User Creation and Database Schema")
    print("=" * 60)
    
    # Initialize AuthService
    jwt_manager = JWTManager(secret_key="test", algorithm="HS256")
    auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, NOTION_PARENT_PAGE_ID)
    
    # Create a unique test email
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"schema_test_{timestamp}@example.com"
    test_password = "testpassword123"
    test_name = f"Schema Test User {timestamp}"
    
    print(f"📧 Test email: {test_email}")
    print(f"👤 Test name: {test_name}")
    print()
    
    try:
        # Register the new user
        print("🔧 Registering new user...")
        user = auth_service.register_user(
            email=test_email,
            password=test_password,
            full_name=test_name,
            role="user"
        )
        
        print(f"✅ User registered successfully!")
        print(f"   User ID: {user.user_id}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Task Database ID: {user.task_database_id}")
        print()
        
        if not user.task_database_id:
            print("❌ User was created but no task database was assigned")
            return None
            
        # Check the database schema
        print("🔍 Checking task database schema...")
        client = Client(auth=NOTION_TOKEN)
        
        try:
            database = client.databases.retrieve(database_id=user.task_database_id)
            properties = database['properties']
            
            print(f"📋 Database title: {database['title'][0]['text']['content']}")
            print(f"📋 Found {len(properties)} properties:")
            print()
            
            expected_properties = [
                "Task", "Status", "Priority", "Category", "Date", 
                "Due Date", "Notes", "Employee", "Is Recurring", "Reminder Sent"
            ]
            
            for prop_name, prop_data in properties.items():
                prop_type = prop_data['type']
                print(f"  ✅ {prop_name} ({prop_type})")
                
                # Check if it's a select property and show options
                if prop_type == 'select' and 'select' in prop_data:
                    options = prop_data['select']['options']
                    option_names = [opt['name'] for opt in options]
                    print(f"      Options: {', '.join(option_names)}")
            
            print()
            
            # Check for missing properties
            missing_properties = []
            for expected_prop in expected_properties:
                if expected_prop not in properties:
                    missing_properties.append(expected_prop)
            
            if missing_properties:
                print(f"❌ Missing properties: {', '.join(missing_properties)}")
            else:
                print("✅ All expected properties are present!")
                
            return user
            
        except Exception as e:
            print(f"❌ Error retrieving database schema: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_gmail_with_new_user(user):
    """Test Gmail processing with the newly created user."""
    
    if not user:
        print("❌ No user provided for Gmail test")
        return
        
    print("\n📧 Testing Gmail Processing with New User")
    print("=" * 50)
    
    # Test email content
    test_email_content = """
From: Test User
Date: 2024-01-15

Subject: Daily Update

Today I completed the following tasks:
- Finished the quarterly report
- Started working on the new feature
- Had a meeting with the team about project timeline
    """
    
    print(f"📧 Test email content:\n{test_email_content}")
    print()
    
    try:
        from core.task_extractor import extract_tasks_from_update
        from core.task_processor import insert_or_update_task
        from core import fetch_notion_tasks
        
        # Extract tasks from email
        extracted_tasks = extract_tasks_from_update(test_email_content)
        print(f"📋 Extracted {len(extracted_tasks)} tasks")
        
        if extracted_tasks:
            # Get existing tasks from user's database
            existing_tasks = fetch_notion_tasks(database_id=user.task_database_id)
            print(f"📊 Found {len(existing_tasks)} existing tasks in user's database")
            
            # Process each task
            for i, task in enumerate(extracted_tasks, 1):
                print(f"  Processing task {i}: {task.get('task', 'Unknown')}")
                
                log_output = []
                success, message = insert_or_update_task(
                    database_id=user.task_database_id,
                    task=task,
                    existing_tasks=existing_tasks,
                    log_output=log_output
                )
                
                if success:
                    print(f"    ✅ Success: {message}")
                else:
                    print(f"    ❌ Failed: {message}")
                    
                # Print any log messages
                for log_msg in log_output:
                    print(f"    📝 {log_msg}")
                    
        print()
        print("✅ Gmail test completed!")
        
    except Exception as e:
        print(f"❌ Error in Gmail test: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_user(user):
    """Clean up the test user (optional)."""
    if not user:
        return
        
    print(f"\n🧹 Test user cleanup:")
    print(f"   Email: {user.email}")
    print(f"   Task Database ID: {user.task_database_id}")
    print("   Note: You may want to manually delete this user and database from Notion")

if __name__ == "__main__":
    print("🚀 Starting New User Schema Test")
    print()
    
    # Test new user creation and schema
    new_user = test_new_user_creation()
    
    if new_user:
        # Test Gmail functionality with the new user
        test_gmail_with_new_user(new_user)
        
        # Cleanup info
        cleanup_test_user(new_user)
    
    print("\n🏁 Test completed!") 
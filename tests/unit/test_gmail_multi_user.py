#!/usr/bin/env python3
"""
Test script to verify Gmail functionality with multi-user architecture.
This script simulates email processing for different users to ensure
each user's tasks go to their own database.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
from core.services.auth_service import AuthService
from core.security.jwt_utils import JWTManager
from core.task_extractor import extract_tasks_from_update
from core.task_processor import insert_or_update_task
from core import fetch_notion_tasks

def test_gmail_multi_user():
    """Test Gmail processing with multiple users."""
    
    print("🧪 Testing Gmail Multi-User Functionality")
    print("=" * 50)
    
    # Initialize AuthService
    jwt_manager = JWTManager(secret_key="test", algorithm="HS256")
    auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
    
    # Test users (replace with actual user emails from your system)
    test_users = [
        "test_user_20250620_080123@example.com"
    ]
    
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
    
    for user_email in test_users:
        print(f"👤 Testing for user: {user_email}")
        
        try:
            # Look up user
            user = auth_service.get_user_by_email(user_email)
            if not user:
                print(f"❌ User {user_email} not found in the system")
                continue
                
            print(f"✅ User found: {user.full_name}")
            
            if not user.task_database_id:
                print(f"❌ User {user_email} does not have a task database configured")
                continue
                
            print(f"✅ User has task database: {user.task_database_id}")
            
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
            
        except Exception as e:
            print(f"❌ Error processing for user {user_email}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("🏁 Test completed!")

def test_user_lookup():
    """Test user lookup functionality."""
    
    print("🔍 Testing User Lookup")
    print("=" * 30)
    
    # Initialize AuthService
    jwt_manager = JWTManager(secret_key="test", algorithm="HS256")
    auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
    
    # Get all users
    try:
        users = auth_service.get_all_users()
        print(f"📊 Found {len(users)} total users in the system")
        
        for user in users:
            print(f"👤 {user.full_name} ({user.email})")
            if user.task_database_id:
                print(f"   📋 Task DB: {user.task_database_id}")
            else:
                print(f"   ⚠️  No task database configured")
            print()
            
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Gmail Multi-User Tests")
    print()
    
    # Test user lookup first
    test_user_lookup()
    
    print()
    print("=" * 60)
    print()
    
    # Test Gmail processing
    test_gmail_multi_user() 
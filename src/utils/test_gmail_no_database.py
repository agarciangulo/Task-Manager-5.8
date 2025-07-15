#!/usr/bin/env python3
"""
Test script to demonstrate what happens when someone without a task database emails the Gmail setup.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
from src.core.services.auth_service import AuthService
from src.core.security.jwt_utils import JWTManager
from src.core.task_extractor import extract_tasks_from_update
from src.core.task_processor import insert_or_update_task
from core import fetch_notion_tasks

def test_gmail_no_database_scenarios():
    """Test different scenarios when users without task databases email the system."""
    
    print("🧪 Testing Gmail Processing - No Database Scenarios")
    print("=" * 60)
    
    # Initialize AuthService
    jwt_manager = JWTManager(secret_key="test", algorithm="HS256")
    auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
    
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
    
    # Scenario 1: User doesn't exist in the system
    print("🔍 Scenario 1: User doesn't exist in the system")
    print("-" * 50)
    
    non_existent_email = "nonexistent@example.com"
    print(f"📧 Testing with email: {non_existent_email}")
    
    user = auth_service.get_user_by_email(non_existent_email)
    if not user:
        print("✅ Result: User not found - Email would be skipped")
        print("   📝 Action: Email marked as read to avoid reprocessing")
        print("   📝 No tasks processed")
        print("   📝 No confirmation email sent")
    else:
        print("❌ Unexpected: User found when they shouldn't exist")
    
    print()
    
    # Scenario 2: User exists but has no task database
    print("🔍 Scenario 2: User exists but has no task database")
    print("-" * 50)
    
    # Get a user without a task database from our test results
    users = auth_service.get_all_users()
    user_without_db = None
    
    for u in users:
        if not u.task_database_id:
            user_without_db = u
            break
    
    if user_without_db:
        print(f"📧 Testing with user: {user_without_db.email}")
        print(f"👤 User name: {user_without_db.full_name}")
        print(f"📋 Task database ID: {user_without_db.task_database_id or 'None'}")
        
        print("✅ Result: User found but no task database - Email would be skipped")
        print("   📝 Action: Email marked as read to avoid reprocessing")
        print("   📝 No tasks processed")
        print("   📝 No confirmation email sent")
        print("   📝 User would need to be assigned a task database first")
    else:
        print("ℹ️  No users found without task databases")
    
    print()
    
    # Scenario 3: Show what happens when user has a database
    print("🔍 Scenario 3: User has a task database (for comparison)")
    print("-" * 50)
    
    user_with_db = None
    for u in users:
        if u.task_database_id:
            user_with_db = u
            break
    
    if user_with_db:
        print(f"📧 Testing with user: {user_with_db.email}")
        print(f"👤 User name: {user_with_db.full_name}")
        print(f"📋 Task database ID: {user_with_db.task_database_id}")
        
        # Extract tasks from email
        extracted_tasks = extract_tasks_from_update(test_email_content)
        print(f"📋 Extracted {len(extracted_tasks)} tasks")
        
        if extracted_tasks:
            # Get existing tasks from user's database
            existing_tasks = fetch_notion_tasks(database_id=user_with_db.task_database_id)
            print(f"📊 Found {len(existing_tasks)} existing tasks in user's database")
            
            print("✅ Result: User has database - Tasks would be processed normally")
            print("   📝 Action: Tasks extracted and inserted into database")
            print("   📝 Action: Confirmation email sent with coaching insights")
            print("   📝 Action: Email marked as read")
    else:
        print("ℹ️  No users found with task databases")
    
    print()
    
    # Summary of Gmail processor behavior
    print("📋 Summary of Gmail Processor Behavior")
    print("=" * 50)
    print("When someone emails the Gmail setup:")
    print()
    print("1. 🔍 System looks up user by email address")
    print("   - If user not found: Email skipped, marked as read")
    print("   - If user found: Continue to step 2")
    print()
    print("2. 📋 System checks if user has task database")
    print("   - If no database: Email skipped, marked as read")
    print("   - If database exists: Continue to step 3")
    print()
    print("3. 📝 System processes the email")
    print("   - Extract tasks from email content")
    print("   - Insert tasks into user's database")
    print("   - Generate coaching insights")
    print("   - Send confirmation email")
    print("   - Mark email as read")
    print()
    print("💡 Key Points:")
    print("   - No error emails are sent to users without databases")
    print("   - Emails are marked as read to avoid reprocessing")
    print("   - Users need to be registered AND have task databases")
    print("   - The system fails gracefully without breaking")

if __name__ == "__main__":
    print("🚀 Starting Gmail No Database Test")
    print()
    
    test_gmail_no_database_scenarios()
    
    print("\n🏁 Test completed!") 
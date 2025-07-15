#!/usr/bin/env python3
"""
Core Workflow Test for Task Manager
Tests the essential workflow: user creation → task extraction → task insertion → coaching insights
"""
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import (
    NOTION_TOKEN, 
    NOTION_USERS_DB_ID, 
    NOTION_PARENT_PAGE_ID,
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD
)
from src.core.services.auth_service import AuthService
from src.core.security.jwt_utils import JWTManager
from src.core.task_extractor import extract_tasks_from_update
from src.core.task_processor import insert_or_update_task
from core import fetch_notion_tasks
from src.core.ai.insights import get_coaching_insight

# Test configuration
TEST_USER_EMAIL = f"core_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_NAME = f"Core Test User {datetime.now().strftime('%H%M%S')}"

class CoreWorkflowTest:
    """Core workflow test runner."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_user = None
        self.test_results = {
            "user_creation": False,
            "task_database_creation": False,
            "task_extraction": False,
            "task_insertion": False,
            "coaching_insights": False,
            "email_simulation": False
        }
        
        # Initialize services
        self.jwt_manager = JWTManager(secret_key="test", algorithm="HS256")
        self.auth_service = AuthService(
            NOTION_TOKEN, 
            NOTION_USERS_DB_ID, 
            self.jwt_manager, 
            NOTION_PARENT_PAGE_ID
        )
        
    def run_all_tests(self):
        """Run the complete core workflow test suite."""
        print("🚀 Starting Core Workflow Test")
        print("=" * 60)
        print(f"📧 Test User Email: {TEST_USER_EMAIL}")
        print(f"👤 Test User Name: {TEST_USER_NAME}")
        print()
        
        try:
            # Step 1: Create user
            self.test_user_creation()
            
            # Step 2: Verify task database creation
            self.test_task_database_creation()
            
            # Step 3: Test task extraction
            self.test_task_extraction()
            
            # Step 4: Test task insertion
            self.test_task_insertion()
            
            # Step 5: Test coaching insights generation
            self.test_coaching_insights()
            
            # Step 6: Test email simulation
            self.test_email_simulation()
            
            # Step 7: Print results
            self.print_results()
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            self.cleanup()
    
    def test_user_creation(self):
        """Test user creation directly via AuthService."""
        print("1️⃣ Testing User Creation")
        print("-" * 30)
        
        try:
            # Create user directly via AuthService
            user = self.auth_service.register_user(
                email=TEST_USER_EMAIL,
                password=TEST_USER_PASSWORD,
                full_name=TEST_USER_NAME,
                role="user"
            )
            
            print(f"✅ User created successfully!")
            print(f"   User ID: {user.user_id}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Task Database ID: {user.task_database_id}")
            
            # Store user info for later tests
            self.test_user = {
                "email": TEST_USER_EMAIL,
                "user_id": user.user_id,
                "full_name": TEST_USER_NAME,
                "task_database_id": user.task_database_id
            }
            
            self.test_results["user_creation"] = True
            return True
                
        except Exception as e:
            print(f"❌ Error in user creation: {e}")
            return False
    
    def test_task_database_creation(self):
        """Test that task database was created for the user."""
        print("\n2️⃣ Testing Task Database Creation")
        print("-" * 30)
        
        if not self.test_user:
            print("❌ No test user available")
            return False
        
        try:
            # Verify user has task database
            user = self.auth_service.get_user_by_email(TEST_USER_EMAIL)
            if not user:
                print("❌ User not found in database")
                return False
            
            if not user.task_database_id:
                print("❌ User does not have task database")
                return False
            
            print(f"✅ Task database created successfully!")
            print(f"   Database ID: {user.task_database_id}")
            
            # Update our test user info
            self.test_user["task_database_id"] = user.task_database_id
            
            self.test_results["task_database_creation"] = True
            return True
            
        except Exception as e:
            print(f"❌ Error verifying task database: {e}")
            return False
    
    def test_task_extraction(self):
        """Test task extraction from simulated email content."""
        print("\n3️⃣ Testing Task Extraction")
        print("-" * 30)
        
        try:
            # Simulate email content
            test_email_content = f"""
From: {TEST_USER_NAME}
Date: {datetime.now().strftime('%Y-%m-%d')}

Subject: Daily Work Update

Hi team,

Here's my update for today:

- Completed the quarterly report analysis
- Started working on the new authentication feature
- Had a productive meeting with the development team about project timeline
- Fixed three critical bugs in the user interface
- Updated documentation for the API endpoints

Looking forward to tomorrow's sprint planning session.

Best regards,
{TEST_USER_NAME}
            """
            
            print("📧 Test email content:")
            print(test_email_content)
            print()
            
            # Extract tasks from email
            extracted_tasks = extract_tasks_from_update(test_email_content)
            
            print(f"📋 Extracted {len(extracted_tasks)} tasks:")
            for i, task in enumerate(extracted_tasks, 1):
                print(f"   {i}. {task.get('task', 'Unknown')}")
                print(f"      Status: {task.get('status', 'Unknown')}")
                print(f"      Category: {task.get('category', 'Unknown')}")
                print(f"      Employee: {task.get('employee', 'Unknown')}")
                print()
            
            if extracted_tasks:
                self.extracted_tasks = extracted_tasks
                self.test_email_content = test_email_content
                print("✅ Task extraction successful")
                self.test_results["task_extraction"] = True
                return True
            else:
                print("❌ No tasks extracted")
                return False
                
        except Exception as e:
            print(f"❌ Error in task extraction: {e}")
            return False
    
    def test_task_insertion(self):
        """Test inserting tasks into user's database."""
        print("\n4️⃣ Testing Task Insertion")
        print("-" * 30)
        
        if not hasattr(self, 'extracted_tasks') or not self.test_user:
            print("❌ No extracted tasks or test user available")
            return False
        
        try:
            # Get existing tasks from user's database
            existing_tasks = fetch_notion_tasks(database_id=self.test_user["task_database_id"])
            print(f"📊 Found {len(existing_tasks)} existing tasks in database")
            
            # Process each extracted task
            processed_tasks = []
            for i, task in enumerate(self.extracted_tasks, 1):
                print(f"   Processing task {i}: {task.get('task', 'Unknown')}")
                
                log_output = []
                success, message = insert_or_update_task(
                    database_id=self.test_user["task_database_id"],
                    task=task,
                    existing_tasks=existing_tasks,
                    log_output=log_output
                )
                
                if success:
                    print(f"      ✅ Success: {message}")
                    processed_tasks.append(task)
                else:
                    print(f"      ❌ Failed: {message}")
                
                # Print any log messages
                for log_msg in log_output:
                    print(f"      📝 {log_msg}")
            
            if processed_tasks:
                self.processed_tasks = processed_tasks
                print(f"✅ Successfully processed {len(processed_tasks)} tasks")
                self.test_results["task_insertion"] = True
                return True
            else:
                print("❌ No tasks were processed successfully")
                return False
                
        except Exception as e:
            print(f"❌ Error in task insertion: {e}")
            return False
    
    def test_coaching_insights(self):
        """Test coaching insights generation."""
        print("\n5️⃣ Testing Coaching Insights Generation")
        print("-" * 30)
        
        if not hasattr(self, 'processed_tasks') or not self.test_user:
            print("❌ No processed tasks or test user available")
            return False
        
        try:
            # Get recent tasks for this person
            existing_tasks = fetch_notion_tasks(database_id=self.test_user["task_database_id"])
            recent_tasks = existing_tasks[existing_tasks['employee'] == TEST_USER_NAME]
            
            if len(recent_tasks) > 0:
                # Filter to recent tasks (last 14 days)
                try:
                    if recent_tasks['date'].dtype == 'object':
                        recent_tasks = recent_tasks.copy()
                        recent_tasks['date'] = pd.to_datetime(recent_tasks['date'], errors='coerce')
                    recent_tasks = recent_tasks[recent_tasks['date'] >= datetime.now() - timedelta(days=14)]
                except Exception as date_error:
                    print(f"Error processing dates for coaching insights: {date_error}")
                    # If date processing fails, use all recent tasks
                    recent_tasks = recent_tasks
            
            # Get peer feedback (empty for test)
            peer_feedback = []
            
            # Generate coaching insights
            coaching_insights = get_coaching_insight(
                TEST_USER_NAME, 
                self.processed_tasks, 
                recent_tasks, 
                peer_feedback
            )
            
            if coaching_insights:
                self.coaching_insights = coaching_insights
                print("✅ Coaching insights generated successfully")
                print("📝 Insights preview:")
                print(f"   {coaching_insights[:200]}...")
                self.test_results["coaching_insights"] = True
                return True
            else:
                print("❌ No coaching insights generated")
                return False
                
        except Exception as e:
            print(f"❌ Error generating coaching insights: {e}")
            return False
    
    def test_email_simulation(self):
        """Test email simulation (without actually sending)."""
        print("\n6️⃣ Testing Email Simulation")
        print("-" * 30)
        
        if not hasattr(self, 'processed_tasks'):
            print("❌ No processed tasks available")
            return False
        
        try:
            # Simulate email sending (without actually sending)
            coaching_insights = getattr(self, 'coaching_insights', None)
            
            print("📧 Simulating confirmation email:")
            print(f"   Recipient: {TEST_USER_EMAIL}")
            print(f"   Tasks included: {len(self.processed_tasks)}")
            print(f"   Coaching insights: {'Yes' if coaching_insights else 'No'}")
            
            # Show what the email would contain
            print("\n📄 Email content preview:")
            print(f"Subject: Task Manager: {len(self.processed_tasks)} Tasks Processed")
            print(f"To: {TEST_USER_EMAIL}")
            print(f"From: {GMAIL_ADDRESS}")
            print()
            print("Tasks processed:")
            for i, task in enumerate(self.processed_tasks, 1):
                print(f"  {i}. {task.get('task', 'Unknown')} ({task.get('status', 'Unknown')})")
            
            if coaching_insights:
                print(f"\nCoaching Insights:\n{coaching_insights[:300]}...")
            
            print("✅ Email simulation completed")
            self.test_results["email_simulation"] = True
            return True
                
        except Exception as e:
            print(f"❌ Error in email simulation: {e}")
            return False
    
    def print_results(self):
        """Print test results summary."""
        print("\n📊 Test Results Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Core workflow is working correctly.")
        else:
            print("⚠️ Some tests failed. Please check the logs above.")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"core_workflow_results_{timestamp}.json"
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "test_user": self.test_user,
            "results": self.test_results,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{passed_tests/total_tests*100:.1f}%"
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
    
    def cleanup(self):
        """Clean up test data (optional)."""
        print("\n🧹 Cleanup")
        print("-" * 30)
        print("Note: Test user and tasks remain in the system for manual inspection.")
        print("To clean up manually:")
        print(f"  1. Delete user from Notion users database: {TEST_USER_EMAIL}")
        print(f"  2. Delete task database: {self.test_user.get('task_database_id', 'N/A') if self.test_user else 'N/A'}")

def main():
    """Run the core workflow test."""
    # Check if required environment variables are set
    required_vars = [
        'NOTION_TOKEN',
        'NOTION_USERS_DB_ID', 
        'NOTION_PARENT_PAGE_ID',
        'GMAIL_ADDRESS',
        'GMAIL_APP_PASSWORD'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file and try again.")
        return False
    
    # Run the test
    test_runner = CoreWorkflowTest()
    test_runner.run_all_tests()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
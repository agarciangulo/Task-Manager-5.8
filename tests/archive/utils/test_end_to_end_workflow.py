#!/usr/bin/env python3
"""
End-to-End Workflow Test for Task Manager
Tests the complete process: user creation → email processing → task extraction → confirmation email
"""
import os
import sys
import time
import json
import requests
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
BASE_URL = "http://localhost:5001"
TEST_USER_EMAIL = f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_NAME = f"E2E Test User {datetime.now().strftime('%H%M%S')}"

class EndToEndTest:
    """End-to-end test runner for the complete workflow."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_user = None
        self.test_results = {
            "user_creation": False,
            "task_database_creation": False,
            "email_processing": False,
            "task_extraction": False,
            "task_insertion": False,
            "coaching_insights": False,
            "confirmation_email": False
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
        """Run the complete end-to-end test suite."""
        print("🚀 Starting End-to-End Workflow Test")
        print("=" * 80)
        print(f"📧 Test User Email: {TEST_USER_EMAIL}")
        print(f"👤 Test User Name: {TEST_USER_NAME}")
        print(f"🔗 Base URL: {BASE_URL}")
        print()
        
        try:
            # Step 1: Create user
            self.test_user_creation()
            
            # Step 2: Verify task database creation
            self.test_task_database_creation()
            
            # Step 3: Test email processing
            self.test_email_processing()
            
            # Step 4: Test task extraction
            self.test_task_extraction()
            
            # Step 5: Test task insertion
            self.test_task_insertion()
            
            # Step 6: Test coaching insights generation
            self.test_coaching_insights()
            
            # Step 7: Test confirmation email
            self.test_confirmation_email()
            
            # Step 8: Verify final state
            self.verify_final_state()
            
            # Step 9: Print results
            self.print_results()
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            self.cleanup()
    
    def test_user_creation(self):
        """Test user creation via API."""
        print("1️⃣ Testing User Creation")
        print("-" * 40)
        
        try:
            # Create user via API
            user_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME,
                "role": "user"
            }
            
            response = requests.post(f"{BASE_URL}/api/register", json=user_data)
            
            if response.status_code == 201:
                user_info = response.json().get("user", {})
                print(f"✅ User created successfully!")
                print(f"   User ID: {user_info.get('user_id', 'N/A')}")
                print(f"   Full Name: {user_info.get('full_name', 'N/A')}")
                print(f"   Task Database ID: {user_info.get('task_database_id', 'N/A')}")
                
                # Store user info for later tests
                self.test_user = {
                    "email": TEST_USER_EMAIL,
                    "user_id": user_info.get('user_id'),
                    "full_name": TEST_USER_NAME,
                    "task_database_id": user_info.get('task_database_id')
                }
                
                self.test_results["user_creation"] = True
                return True
            else:
                print(f"❌ User creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error in user creation: {e}")
            return False
    
    def test_task_database_creation(self):
        """Test that task database was created for the user."""
        print("\n2️⃣ Testing Task Database Creation")
        print("-" * 40)
        
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
    
    def test_email_processing(self):
        """Test email processing simulation."""
        print("\n3️⃣ Testing Email Processing")
        print("-" * 40)
        
        if not self.test_user:
            print("❌ No test user available")
            return False
        
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
            
            # Store for later tests
            self.test_email_content = test_email_content
            
            print("✅ Email content prepared successfully")
            self.test_results["email_processing"] = True
            return True
            
        except Exception as e:
            print(f"❌ Error in email processing: {e}")
            return False
    
    def test_task_extraction(self):
        """Test task extraction from email content."""
        print("\n4️⃣ Testing Task Extraction")
        print("-" * 40)
        
        if not hasattr(self, 'test_email_content'):
            print("❌ No test email content available")
            return False
        
        try:
            # Extract tasks from email
            extracted_tasks = extract_tasks_from_update(self.test_email_content)
            
            print(f"📋 Extracted {len(extracted_tasks)} tasks:")
            for i, task in enumerate(extracted_tasks, 1):
                print(f"   {i}. {task.get('task', 'Unknown')}")
                print(f"      Status: {task.get('status', 'Unknown')}")
                print(f"      Category: {task.get('category', 'Unknown')}")
                print(f"      Employee: {task.get('employee', 'Unknown')}")
                print()
            
            if extracted_tasks:
                self.extracted_tasks = extracted_tasks
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
        print("\n5️⃣ Testing Task Insertion")
        print("-" * 40)
        
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
        print("\n6️⃣ Testing Coaching Insights Generation")
        print("-" * 40)
        
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
    
    def test_confirmation_email(self):
        """Test confirmation email sending."""
        print("\n7️⃣ Testing Confirmation Email")
        print("-" * 40)
        
        if not hasattr(self, 'processed_tasks'):
            print("❌ No processed tasks available")
            return False
        
        try:
            # Import email sending function
            from gmail_processor import send_confirmation_email
            
            # Send confirmation email
            coaching_insights = getattr(self, 'coaching_insights', None)
            success = send_confirmation_email(
                TEST_USER_EMAIL, 
                self.processed_tasks, 
                coaching_insights
            )
            
            if success:
                print("✅ Confirmation email sent successfully")
                print(f"   Recipient: {TEST_USER_EMAIL}")
                print(f"   Tasks included: {len(self.processed_tasks)}")
                print(f"   Coaching insights: {'Yes' if coaching_insights else 'No'}")
                self.test_results["confirmation_email"] = True
                return True
            else:
                print("❌ Failed to send confirmation email")
                return False
                
        except Exception as e:
            print(f"❌ Error sending confirmation email: {e}")
            return False
    
    def verify_final_state(self):
        """Verify the final state of the user's task database."""
        print("\n8️⃣ Verifying Final State")
        print("-" * 40)
        
        if not self.test_user:
            print("❌ No test user available")
            return False
        
        try:
            # Get all tasks from user's database
            all_tasks = fetch_notion_tasks(database_id=self.test_user["task_database_id"])
            
            print(f"📊 Final task count in database: {len(all_tasks)}")
            
            if hasattr(self, 'processed_tasks'):
                print(f"📋 Expected processed tasks: {len(self.processed_tasks)}")
                
                # Check if our processed tasks are in the database
                processed_task_texts = [task.get('task', '') for task in self.processed_tasks]
                database_task_texts = [task.get('task', '') for task in all_tasks]
                
                found_count = 0
                for task_text in processed_task_texts:
                    if task_text in database_task_texts:
                        found_count += 1
                
                print(f"✅ Found {found_count}/{len(processed_task_texts)} processed tasks in database")
                
                if found_count == len(processed_task_texts):
                    print("🎉 All processed tasks successfully stored in database!")
                else:
                    print("⚠️ Some tasks may not have been stored properly")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verifying final state: {e}")
            return False
    
    def print_results(self):
        """Print test results summary."""
        print("\n📊 Test Results Summary")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! End-to-end workflow is working correctly.")
        else:
            print("⚠️ Some tests failed. Please check the logs above.")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"e2e_test_results_{timestamp}.json"
        
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
        print("-" * 40)
        print("Note: Test user and tasks remain in the system for manual inspection.")
        print("To clean up manually:")
        print(f"  1. Delete user from Notion users database: {TEST_USER_EMAIL}")
        print(f"  2. Delete task database: {self.test_user.get('task_database_id', 'N/A') if self.test_user else 'N/A'}")
        print("  3. Check Gmail for confirmation email and delete if needed")

def main():
    """Run the end-to-end test."""
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
    
    # Check if Flask app is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ Flask app is not responding correctly: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ Flask app is not running at {BASE_URL}")
        print("Please start the Flask application and try again.")
        return False
    
    # Run the test
    test_runner = EndToEndTest()
    test_runner.run_all_tests()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
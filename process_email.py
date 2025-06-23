#!/usr/bin/env python3
"""
Simple email processing script to handle emails sent to the task manager.
This script will check Gmail for new emails and process them for task extraction.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gmail_processor import GmailProcessor
from core.task_extractor import extract_tasks_from_update
from core.task_processor import insert_or_update_task
from core import fetch_notion_tasks
from core.ai.insights import get_coaching_insight

def process_recent_emails():
    """Process recent emails from Gmail."""
    print("📧 Processing recent emails...")
    
    try:
        # Initialize Gmail processor
        gmail_processor = GmailProcessor()
        
        # Check if Gmail connection is working
        if not gmail_processor.test_connection():
            print("❌ Failed to connect to Gmail. Please check your credentials.")
            return False
        
        print("✅ Gmail connection successful!")
        
        # Get recent emails (last 24 hours)
        since_date = datetime.now() - timedelta(hours=24)
        emails = gmail_processor.fetch_recent_emails(since_date=since_date)
        
        if not emails:
            print("📭 No recent emails found in the last 24 hours.")
            return True
        
        print(f"📨 Found {len(emails)} recent emails")
        
        # Process each email
        for i, email in enumerate(emails, 1):
            print(f"\n📧 Processing email {i}/{len(emails)}")
            print(f"   From: {email.get('from', 'Unknown')}")
            print(f"   Subject: {email.get('subject', 'No subject')}")
            print(f"   Date: {email.get('date', 'Unknown')}")
            
            # Extract email content
            email_content = email.get('body', '')
            if not email_content:
                print("   ⚠️ No content found in email")
                continue
            
            # Extract tasks from email content
            print("   🔍 Extracting tasks...")
            extracted_tasks = extract_tasks_from_update(email_content)
            
            if not extracted_tasks:
                print("   ⚠️ No tasks found in email")
                continue
            
            print(f"   ✅ Found {len(extracted_tasks)} tasks")
            
            # For now, just display the tasks
            # In a full implementation, you'd save them to the user's database
            for j, task in enumerate(extracted_tasks, 1):
                print(f"      {j}. {task.get('task', 'Unknown')}")
                print(f"         Status: {task.get('status', 'Unknown')}")
                print(f"         Category: {task.get('category', 'Unknown')}")
                print(f"         Employee: {task.get('employee', 'Unknown')}")
            
            # Generate coaching insights
            try:
                coaching_insights = get_coaching_insight(
                    email.get('from', 'User'),
                    extracted_tasks,
                    [],  # No existing tasks for now
                    []
                )
                print(f"   💡 Coaching Insights: {coaching_insights[:100]}...")
            except Exception as e:
                print(f"   ⚠️ Failed to generate coaching insights: {e}")
        
        print(f"\n✅ Email processing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing emails: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_specific_email(email_id=None):
    """Process a specific email by ID."""
    print(f"📧 Processing specific email: {email_id}")
    
    try:
        gmail_processor = GmailProcessor()
        
        if not gmail_processor.test_connection():
            print("❌ Failed to connect to Gmail.")
            return False
        
        # Get the specific email
        email = gmail_processor.get_email_by_id(email_id) if email_id else None
        
        if not email:
            print("❌ Email not found or no email ID provided.")
            return False
        
        print(f"📨 Email found:")
        print(f"   From: {email.get('from', 'Unknown')}")
        print(f"   Subject: {email.get('subject', 'No subject')}")
        print(f"   Date: {email.get('date', 'Unknown')}")
        
        # Extract tasks
        email_content = email.get('body', '')
        extracted_tasks = extract_tasks_from_update(email_content)
        
        if not extracted_tasks:
            print("❌ No tasks found in email")
            return False
        
        print(f"✅ Found {len(extracted_tasks)} tasks:")
        for i, task in enumerate(extracted_tasks, 1):
            print(f"   {i}. {task.get('task', 'Unknown')}")
            print(f"      Status: {task.get('status', 'Unknown')}")
            print(f"      Category: {task.get('category', 'Unknown')}")
            print(f"      Employee: {task.get('employee', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing email: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("🚀 Email Processing Script")
    print("=" * 50)
    
    # Check if environment variables are set
    required_vars = ['GMAIL_ADDRESS', 'GMAIL_APP_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file and try again.")
        return False
    
    # Check command line arguments
    if len(sys.argv) > 1:
        email_id = sys.argv[1]
        return process_specific_email(email_id)
    else:
        return process_recent_emails()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
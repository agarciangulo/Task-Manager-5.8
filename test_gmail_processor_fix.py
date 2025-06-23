#!/usr/bin/env python3
"""
Test to reproduce the gmail_processor.py issue
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.task_extractor import extract_tasks_from_update
from core.task_processor import insert_or_update_task

def test_gmail_processor_issue():
    """Test the exact issue that gmail_processor.py is having."""
    
    print("🔍 Testing gmail_processor.py issue...")
    
    # Simulate the email content that's failing
    test_email = """
    From: Andres Garcia Angulo
    Date: 2025-06-23
    
    Subject: Andres G. Tasks 6.23
    
    Advanced Follow Up agent. Still blocked with Gmail functionality, but progressing well in the logic to not stop
    
    Met with Paula to discuss the progress of the website and Jasper. She is already creating a campaign for attorneys and creating material for the website
    
    Reached out to Cris's husband, a lawyer at his family's law firm
    
    Met with Daniela and Paula to discuss the website blockers and what is needed to publish it
    
    Created 3 blog posts for the MPIV website and sent them to Daniela
    
    Completed Module 2 and Exam of VC University
    
    Attended VC University office hours to connect with students and review material
    
    Researched more about the VCs I will be visiting tomorrow and added them to my report
    
    Sent a message to a friend who is a startup recruiter
    """
    
    print("📤 Extracting tasks...")
    tasks = extract_tasks_from_update(test_email)
    
    print(f"📥 Extracted {len(tasks)} tasks")
    
    if tasks:
        print("✅ Task extraction successful!")
        print("\n📋 Sample task format:")
        sample_task = tasks[0]
        for key, value in sample_task.items():
            print(f"   {key}: {value}")
        
        # Test the task processor with the new format
        print("\n🔧 Testing task processor...")
        log_output = []
        
        # Simulate existing tasks (empty for this test)
        existing_tasks = []
        
        success, message = insert_or_update_task(
            database_id="test_database_id",
            task=sample_task,
            existing_tasks=existing_tasks,
            log_output=log_output,
            batch_mode=True  # Don't actually insert to Notion
        )
        
        print(f"Task processor result: {success}, {message}")
        print("Log output:")
        for log in log_output:
            print(f"   {log}")
            
    else:
        print("❌ No tasks extracted")
    
    return True

if __name__ == "__main__":
    test_gmail_processor_issue() 
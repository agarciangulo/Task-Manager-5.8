#!/usr/bin/env python3
"""
Debug script to test Gemini API response parsing and Notion transformation
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.task_extractor import extract_tasks_from_update
from config import AI_PROVIDER

def test_task_extraction():
    """Test task extraction with Gemini API and Notion transformation."""
    print("🔍 Testing task extraction with Gemini API and Notion transformation...")
    
    if AI_PROVIDER != 'gemini':
        print(f"❌ AI_PROVIDER is set to '{AI_PROVIDER}', not 'gemini'")
        return False
    
    try:
        # Test with a simple email-like text
        test_text = """
        From: John Doe
        Date: 2024-01-01
        
        Completed Activities:
        - Updated the resume with new skills and experience
        - Worked on project documentation
        - Meeting with team about project timeline
        
        Planned Activities:
        - Start working on the new feature
        - Review pull requests
        """
        
        print("📤 Testing task extraction...")
        print(f"Input text length: {len(test_text)} characters")
        
        # Call the task extraction function
        tasks = extract_tasks_from_update(test_text)
        
        print(f"📥 Extracted and transformed {len(tasks)} tasks")
        
        if tasks:
            print("✅ Task extraction and transformation successful!")
            for i, task in enumerate(tasks, 1):
                print(f"\n   Task {i}:")
                print(f"      Task: {task.get('task', 'Unknown')}")
                print(f"      Status: {task.get('status', 'Unknown')}")
                print(f"      Employee: {task.get('employee', 'Unknown')}")
                print(f"      Category: {task.get('category', 'Unknown')}")
                print(f"      Priority: {task.get('priority', 'Unknown')}")
                print(f"      Notes: {task.get('notes', 'Unknown')}")
                print(f"      Date: {task.get('date', 'Unknown')}")
                print(f"      Due Date: {task.get('due_date', 'Unknown')}")
                print(f"      Is Recurring: {task.get('is_recurring', 'Unknown')}")
                print(f"      Reminder Sent: {task.get('reminder_sent', 'Unknown')}")
        else:
            print("❌ No tasks extracted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing task extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_task_extraction()
    sys.exit(0 if success else 1) 
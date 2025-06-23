#!/usr/bin/env python3
"""
Debug script to show the format mismatch between Gemini extraction and Notion expectations
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_format_mismatch():
    """Show the exact format mismatch between Gemini and Notion."""
    
    print("🔍 FORMAT MISMATCH ANALYSIS")
    print("=" * 50)
    
    # What Gemini extracts (from task_extractor.py)
    print("\n📤 GEMINI EXTRACTION FORMAT:")
    print("Expected output from extract_tasks_from_update():")
    gemini_format = [
        {
            "task": "Updated the resume with new skills and experience",
            "status": "Completed",
            "employee": "John Doe", 
            "date": "2024-01-01",
            "category": "General",
            "needs_description": False,
            "suggested_question": ""
        }
    ]
    print(f"Keys: {list(gemini_format[0].keys())}")
    print(f"Sample: {gemini_format[0]}")
    
    # What Notion expects (from user_task_service.py)
    print("\n📥 NOTION EXPECTED FORMAT:")
    print("What create_task_in_user_database() expects:")
    notion_expected = {
        "task": "Updated the resume with new skills and experience",
        "status": "Completed", 
        "employee": "John Doe",
        "date": "2024-01-01",
        "category": "General",
        "priority": "Medium",  # ← MISSING from Gemini
        "due_date": None,      # ← MISSING from Gemini  
        "notes": "",           # ← MISSING from Gemini
        "is_recurring": False, # ← MISSING from Gemini
        "reminder_sent": False # ← MISSING from Gemini
    }
    print(f"Keys: {list(notion_expected.keys())}")
    print(f"Sample: {notion_expected}")
    
    # Show the mismatch
    print("\n❌ FORMAT MISMATCH:")
    gemini_keys = set(gemini_format[0].keys())
    notion_keys = set(notion_expected.keys())
    
    print(f"Gemini extra keys: {gemini_keys - notion_keys}")
    print(f"Notion missing keys: {notion_keys - gemini_keys}")
    print(f"Common keys: {gemini_keys & notion_keys}")
    
    # Show what happens when we try to use Gemini output in Notion
    print("\n🚨 WHAT HAPPENS WHEN GEMINI OUTPUT GOES TO NOTION:")
    gemini_task = gemini_format[0]
    
    # Simulate what Notion service does
    notion_properties = {
        "Task": {
            "title": [{"text": {"content": gemini_task.get("task", "")}}]
        },
        "Status": {
            "select": {"name": gemini_task.get("status", "Not Started")}
        },
        "Priority": {
            "select": {"name": gemini_task.get("priority", "Medium")}  # ← Uses default
        },
        "Category": {
            "rich_text": [{"text": {"content": gemini_task.get("category", "")}}]
        },
        "Date": {
            "date": {"start": gemini_task.get("date")} if gemini_task.get("date") else None
        },
        "Due Date": {
            "date": {"start": gemini_task.get("due_date")} if gemini_task.get("due_date") else None  # ← None
        },
        "Notes": {
            "rich_text": [{"text": {"content": gemini_task.get("notes", "")}}]  # ← Empty
        },
        "Employee": {
            "rich_text": [{"text": {"content": gemini_task.get("employee", "")}}]
        },
        "Is Recurring": {
            "checkbox": gemini_task.get("is_recurring", False)  # ← Uses default
        },
        "Reminder Sent": {
            "checkbox": gemini_task.get("reminder_sent", False)  # ← Uses default
        }
    }
    
    print("Notion will receive these properties:")
    for key, value in notion_properties.items():
        print(f"  {key}: {value}")
    
    print("\n✅ SOLUTION:")
    print("We need to transform Gemini output to match Notion expectations.")
    print("The transformation should:")
    print("1. Keep all Gemini fields (task, status, employee, date, category)")
    print("2. Add missing Notion fields with sensible defaults")
    print("3. Remove Gemini-specific fields (needs_description, suggested_question)")
    
    return True

if __name__ == "__main__":
    show_format_mismatch() 
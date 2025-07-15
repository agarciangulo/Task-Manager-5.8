#!/usr/bin/env python3
"""
Test the markdown removal fix
"""
import re

def test_markdown_removal():
    """Test the markdown removal logic."""
    
    # Simulate the problematic content from your error
    problematic_content = '''```json
[
  {
    "task": "Advanced Follow Up agent. Still blocked with Gmail functionality, but progressing well in the logic to not stop",
    "status": "In Progress",
    "employee": "Andres Garcia Angulo",
    "date": "2025-06-23",
    "category": "MPIV Agents",
    "priority": "Medium",
    "due_date": null,
    "notes": null,
    "is_recurring": false,
    "reminder_sent": false
  }
]
```'''
    
    print("🔍 Testing markdown removal fix...")
    print(f"Original content length: {len(problematic_content)}")
    print(f"Original content preview: {repr(problematic_content[:100])}...")
    
    # Apply the fix
    content = problematic_content
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    content = re.sub(r'^```\s*', '', content)
    content = content.strip()
    
    print(f"After markdown removal, length: {len(content)}")
    print(f"Cleaned content preview: {repr(content[:100])}...")
    
    # Try to parse as JSON
    import json
    try:
        parsed = json.loads(content)
        print(f"✅ JSON parsing successful! Found {len(parsed)} items")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        return False

if __name__ == "__main__":
    test_markdown_removal() 
"""
Task extraction functionality for Task Manager.
Handles extracting structured tasks from freeform text with AI-based context evaluation.
"""
import json
import re
import ast
import traceback
from dateutil import parser
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import (
    GEMINI_API_KEY,
    MIN_TASK_LENGTH, 
    DEBUG_MODE,
    CHAT_MODEL,
    ENABLE_CHAT_VERIFICATION,
    AI_PROVIDER
)

# Import security manager for protecting sensitive data
from plugins import plugin_manager

# Import Gemini client at module level
try:
    from core.gemini_client import client as gemini_client
except ImportError:
    gemini_client = None
    print("Warning: Could not import Gemini client")

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def get_ai_response(prompt: str) -> str:
    """Get response from Gemini API."""
    try:
        if not gemini_client:
            raise Exception("Gemini client not available")
        
        # Use Gemini's native API
        response_text = gemini_client.generate_content(
            prompt,
            temperature=0.3
        )
        
        return response_text
        
    except Exception as e:
        print(f"Error getting AI response from Gemini: {e}")
        return f"Error: {str(e)}"

def extract_tasks_from_update(text: str) -> List[Dict[str, Any]]:
    """
    Extract structured tasks from freeform text with integrated context evaluation.
    
    Args:
        text: The text to extract tasks from.
        
    Returns:
        List[Dict[str, Any]]: List of task dictionaries with context evaluation.
    """
    if not text:
        return []

    print("Starting task extraction with integrated context evaluation...")
    
    # Initialize tasks as empty list to prevent UnboundLocalError
    tasks = []
    
    # Get the project protection plugin if available
    protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
    
    # Apply protection to the input text if the plugin is available
    protected_text = text
    if protection_plugin and protection_plugin.enabled:
        # Only protect project names that are already known
        # New projects will be discovered during processing and protected afterward
        protected_text = protection_plugin.protect_text(text)

    # SIMPLIFIED: Clean prompt that asks for parseable JSON
    prompt = f"""Extract tasks from this text and return ONLY a clean JSON array.

INPUT TEXT:
{protected_text}

REQUIREMENTS:
- Extract all actionable tasks
- Identify the person who did the work
- Determine task status (Completed/In Progress/Pending/Blocked)
- Assign appropriate categories
- Use today's date if no date is specified

OUTPUT FORMAT:
Return ONLY a JSON array like this (no markdown, no explanations):
[
  {{
    "task": "Task description",
    "status": "Completed",
    "employee": "Employee name", 
    "date": "YYYY-MM-DD",
    "category": "Project name"
  }}
]

RULES:
- Return ONLY the JSON array, nothing else
- Use lowercase keys: task, status, employee, date, category
- Use today's date if no date is found
- Keep task descriptions clear and specific
- Assign "General" category if no specific project is mentioned
"""

    try:
        print(f"Calling Gemini API for combined extraction and evaluation...")
        content = get_ai_response(prompt)
        
        if content.startswith("Error:"):
            print(f"Gemini API error: {content}")
            return []

        print(f"Received response from Gemini. Length: {len(content)}")

        # Remove markdown code blocks if present (robust)
        content = re.sub(r'```(?:\w+)?\s*([\s\S]*?)```', r'\1', content)
        content = content.strip()

        # SIMPLIFIED: Parse clean JSON
        try:
            tasks = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parse failed: {e}")
            return []

        # Ensure tasks is a list
        if not isinstance(tasks, list):
            print(f"Parsed result is not a list: {type(tasks)}")
            return []

        # SIMPLIFIED: Validate and process tasks
        valid_tasks = []
        for i, task in enumerate(tasks):
            try:
                if not isinstance(task, dict):
                    print(f"Task {i} is not a dictionary: {type(task)}")
                    continue

                # Ensure all required keys exist with defaults
                required_keys = ["task", "status", "employee", "date", "category"]
                for key in required_keys:
                    if key not in task:
                        if key == "status":
                            task[key] = "Completed"
                        elif key == "category":
                            task[key] = "General"
                        elif key == "date":
                            task[key] = datetime.now().strftime("%Y-%m-%d")
                        else:
                            print(f"Task {i} missing required key: {key}")
                            continue

                # Ensure task description exists
                if not task["task"]:
                    print(f"Task {i} has empty description")
                    continue

                # Standardize date format
                if isinstance(task["date"], str):
                    try:
                        date_obj = parser.parse(task["date"])
                        task["date"] = date_obj.strftime("%Y-%m-%d")
                    except Exception as e:
                        print(f"Date parsing error for task {i}: {e}")
                        task["date"] = datetime.now().strftime("%Y-%m-%d")

                valid_tasks.append(task)

            except Exception as e:
                print(f"Error processing task {i}: {e}")
                continue

        print(f"Validated {len(valid_tasks)} tasks")
        
        # Unprotect tasks before returning them
        if protection_plugin and protection_plugin.enabled:
            try:
                # Unprotect the tasks
                valid_tasks = protection_plugin.unprotect_task_list(valid_tasks)
                # Also unprotect task descriptions
                for task in valid_tasks:
                    if 'task' in task and task['task']:
                        task['task'] = protection_plugin.unprotect_text(task['task'])
            except Exception as e:
                print(f"Error unprotecting tasks in extract_tasks_from_update: {e}")
        
        return valid_tasks

    except Exception as e:
        print(f"Error in extract_tasks_from_update: {traceback.format_exc()}")
        return []
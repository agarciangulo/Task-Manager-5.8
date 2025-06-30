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

    # ADVANCED: Comprehensive prompt with vague task detection
    prompt = f"""You are TaskExtractor, an expert system that extracts structured task updates from both formal and casual work logs, emails, and messages.

YOUR TASK:
Extract actionable tasks from the provided text, which may be in various formats (formal reports, casual updates, bullet points, etc.). Follow these precise steps:

1. TEXT ANALYSIS:
   - Identify the main author of the update
   - Look for any date information
   - Recognize different formats (bullet points, paragraphs, categories, etc.)
   - Handle both formal and casual language

2. SENDER IDENTIFICATION:
   - Extract the full name of the person who performed the tasks
   - Look for patterns like "From:", email signatures, or introductory lines
   - If no name is found, use the email sender's name

3. TASK EXTRACTION STRATEGIES:
   - Look for tasks in any format: bullet points, paragraphs, categories, etc.
   - Extract tasks from both completed and planned sections
   - Recognize tasks even without explicit "Completed" or "Planned" labels
   - Identify action verbs to determine what work was performed
   - Ignore non-task information like greetings and signatures
   - IMPORTANT: Extract ALL items as tasks, even single words like "Resume" or "Training"

4. VAGUE TASK DETECTION (CRITICAL):
   - Flag tasks as needing more context (set needs_description=true) if they match ANY of these criteria:
     * Single-word tasks (e.g., "Resume", "Training", "Meeting")
     * Short phrases without specific details (e.g., "VC University", "Project work")
     * Generic descriptions (e.g., "Worked on project", "Made updates")
     * Tasks missing what was actually done (e.g., "Resume" instead of "Updated resume")
     * Tasks without clear deliverables or outcomes
   - For each vague task, generate a specific follow-up question asking for:
     * What specifically was done
     * What was the outcome or progress made
     * Any relevant details about the work

5. STATUS DETERMINATION - CLASSIFY AS:
   - "Completed": Tasks described in past tense or marked as done
   - "In Progress": Work mentioned as started but not finished
   - "Pending": Tasks mentioned without completion status
   - "Blocked": Tasks explicitly mentioned as blocked

6. DATE EXTRACTION:
   - Extract the date when tasks were performed from the title / subject line of the email
   - If not explicitly mentioned, use the email/update date
   - Standardize all dates to YYYY-MM-DD format
   - For updates with multiple dates, use the most recent relevant date

7. CATEGORIZATION:
   - Assign each task to a category based on context
   - Use section headers, indentation, or prefix labels to determine categories
   - If a task mentions multiple categories, prefer the most specific one
   - If no category is explicitly mentioned, use "General"

OUTPUT FORMAT:
Return a list of tasks in this exact format for Notion integration:
[
    {{
        "title": "Short, descriptive title",
        "task": "Detailed description of the task",
        "status": "Completed/In Progress/Not Started/On Hold",
        "employee": "Full name of the person who did the task",
        "date": "YYYY-MM-DD",
        "category": "Category name",
        "priority": "Low/Medium/High/Urgent",
        "due_date": null,
        "notes": "Additional notes or clarification questions for vague tasks",
        "is_recurring": false,
        "reminder_sent": false
    }},
    ...
]

IMPORTANT FORMATTING RULES:
- Generate a concise, descriptive title that summarizes the task
- Use "Not Started" instead of "Pending" for status
- Use "On Hold" instead of "Blocked" for status  
- Set priority to "Medium" by default unless clearly high/urgent
- Set due_date to null (no due dates from email extraction)
- Set is_recurring and reminder_sent to false
- For vague tasks, put the suggested question in the "notes" field
- Always use double quotes for JSON strings
- Use null (not "null") for empty values

EXAMPLE TITLES:
1. Task: "Worked on MPIV AI Agents; Struggled to launch the application into a public URL"
   Title: "MPIV AI Agents - App Launch Troubleshooting"

2. Task: "Met with Paula to discuss the progress of the website and Jasper"
   Title: "Paula Meeting - Website & Jasper Progress"

3. Task: "Completed Module 2 and Exam of VC University"
   Title: "VC University - Module 2 & Exam Complete"

4. Task: "Resume"
   Title: "Resume Update"

INPUT TEXT:
{protected_text}

Remember:
- Extract ALL tasks, even single words or short phrases
- Flag ANY task that lacks specific details about what was done
- Generate specific, contextual follow-up questions for vague tasks
- Use context clues to determine status and categories
- If a task is ambiguous, make reasonable assumptions but still flag for verification
- Always return a list, even if empty
"""

    try:
        print(f"Calling Gemini API for combined extraction and evaluation...")
        content = get_ai_response(prompt)
        
        if content.startswith("Error:"):
            print(f"Gemini API error: {content}")
            return []

        print(f"Received response from Gemini. Length: {len(content)}")
        print(f"Raw response preview: {repr(content[:200])}...")

        # Remove markdown code blocks if present (robust)
        # First, try to remove the outer ```json and ``` markers
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        # Also handle cases without language specification
        content = re.sub(r'^```\s*', '', content)
        content = content.strip()
        print(f"After markdown removal, length: {len(content)}")
        print(f"Cleaned content preview: {repr(content[:200])}...")

        # Parse JSON with multiple fallback methods
        tasks = None
        
        # Method 1: Direct JSON parsing
        try:
            tasks = json.loads(content)
            print("Direct JSON parsing successful!")
        except json.JSONDecodeError as e:
            print(f"Direct JSON parse failed: {e}")
            print(f"Content that failed to parse: {repr(content)}")
            
            # Method 2: Try to extract complete JSON objects from truncated response
            try:
                print("Attempting to extract complete JSON objects from truncated response...")
                # Find all complete JSON objects in the array
                # Pattern to match complete JSON objects with all required fields
                object_pattern = r'\{\s*"[^"]+"\s*:\s*(?:"[^"]*"|null|true|false|\d+)\s*(?:,\s*"[^"]+"\s*:\s*(?:"[^"]*"|null|true|false|\d+)\s*)*\}'
                matches = re.findall(object_pattern, content)
                
                if matches:
                    # Reconstruct a valid JSON array
                    json_array = '[' + ','.join(matches) + ']'
                    tasks = json.loads(json_array)
                    print(f"Extracted {len(tasks)} complete JSON objects from truncated response!")
                else:
                    print("No complete JSON objects found")
            except Exception as e:
                print(f"Complete object extraction failed: {e}")
                
                # Method 3: More aggressive JSON extraction
                try:
                    print("Attempting aggressive JSON extraction...")
                    # Look for the start of the array and extract everything until we hit a parsing error
                    start_idx = content.find('[')
                    if start_idx != -1:
                        # Try to find the end of the array by counting brackets
                        bracket_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(content[start_idx:], start_idx):
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if end_idx > start_idx:
                            json_content = content[start_idx:end_idx]
                            # Try to fix common JSON issues
                            json_content = json_content.replace("'", '"')  # Replace single quotes
                            json_content = re.sub(r',\s*}', '}', json_content)  # Remove trailing commas
                            json_content = re.sub(r',\s*]', ']', json_content)  # Remove trailing commas in arrays
                            
                            tasks = json.loads(json_content)
                            print(f"Aggressive extraction successful! Found {len(tasks)} tasks")
                        else:
                            print("Could not find end of JSON array")
                    else:
                        print("No JSON array start found")
                except Exception as e:
                    print(f"Aggressive extraction failed: {e}")
                    
                    # Method 4: Handle specific truncation pattern
                    try:
                        print("Attempting to handle specific truncation pattern...")
                        # Look for the pattern where the JSON is cut off mid-object
                        # Find all complete objects before the truncation
                        object_pattern = r'\{\s*"[^"]+"\s*:\s*(?:"[^"]*"|null|true|false|\d+)\s*(?:,\s*"[^"]+"\s*:\s*(?:"[^"]*"|null|true|false|\d+)\s*)*\}'
                        matches = re.findall(object_pattern, content)
                        
                        if matches:
                            # Reconstruct a valid JSON array
                            json_array = '[' + ','.join(matches) + ']'
                            tasks = json.loads(json_array)
                            print(f"Truncation pattern extraction successful! Found {len(tasks)} tasks")
                        else:
                            print("No complete objects found in truncation pattern")
                    except Exception as e:
                        print(f"Truncation pattern extraction failed: {e}")
                        
                        # Method 5: Extract array with regex
                        try:
                            print("Attempting to extract JSON array with regex...")
                            match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
                            if match:
                                json_array = match.group(0).replace("'", '"')
                                tasks = json.loads(json_array)
                                print("Regex extraction successful!")
                            else:
                                print("No JSON array found in content")
                        except Exception as e:
                            print(f"Regex extraction failed: {e}")
                            
                            # Method 6: Fall back to safer eval
                            try:
                                print("Attempting eval with ast...")
                                tasks = ast.literal_eval(content)
                                print("AST literal_eval successful!")
                            except Exception as e:
                                print(f"AST literal_eval failed: {e}")
                                
                                # Final fallback: Try eval directly
                                try:
                                    print("Last resort: direct eval...")
                                    tasks = eval(content)
                                    print("Direct eval successful!")
                                except Exception as e:
                                    print(f"All parsing methods failed: {e}")
                                    print(f"Final content that couldn't be parsed: {repr(content)}")
                                    return []

        # Ensure tasks is a list
        if not isinstance(tasks, list):
            print(f"Parsed result is not a list: {type(tasks)}")
            return []

        # Validate and process tasks with advanced features
        valid_tasks = []
        for i, task in enumerate(tasks):
            try:
                if not isinstance(task, dict):
                    print(f"Task {i} is not a dictionary: {type(task)}")
                    continue

                # Ensure all required keys exist with defaults
                required_keys = ["title", "task", "status", "employee", "date", "category", "priority", "due_date", "notes", "is_recurring", "reminder_sent"]
                for key in required_keys:
                    if key not in task:
                        if key == "title":
                            # Generate a simple title from the task description
                            task_desc = task.get("task", "")
                            if task_desc:
                                # Take first 50 characters and clean up
                                title = task_desc[:50].strip()
                                if len(task_desc) > 50:
                                    title = title.rsplit(' ', 1)[0]  # Don't cut words
                                task[key] = title
                            else:
                                task[key] = "Untitled Task"
                        elif key == "status":
                            task[key] = "Not Started"
                        elif key == "category":
                            task[key] = "General"
                        elif key == "priority":
                            task[key] = "Medium"
                        elif key == "date":
                            task[key] = datetime.now().strftime("%Y-%m-%d")
                        elif key == "due_date":
                            task[key] = None
                        elif key == "notes":
                            task[key] = ""
                        elif key == "is_recurring":
                            task[key] = False
                        elif key == "reminder_sent":
                            task[key] = False
                        else:
                            print(f"Task {i} missing required key: {key}")
                            continue

                # Ensure task description exists
                if not task["task"]:
                    print(f"Task {i} has empty description")
                    continue

                # Ensure title exists and is not too long
                if not task.get("title"):
                    task["title"] = task["task"][:50] if task["task"] else "Untitled Task"
                elif len(task["title"]) > 50:
                    task["title"] = task["title"][:50].rsplit(' ', 1)[0]

                # Handle legacy fields if they exist (for backward compatibility)
                if "needs_description" in task and task["needs_description"]:
                    suggested_question = task.get("suggested_question", "")
                    if suggested_question and not task.get("notes"):
                        task["notes"] = f"Needs clarification: {suggested_question}"
                
                # Remove legacy fields
                task.pop("needs_description", None)
                task.pop("suggested_question", None)

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
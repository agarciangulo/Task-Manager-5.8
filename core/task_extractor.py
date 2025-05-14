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
import httpx

from config import (
    OPENAI_API_KEY,
    MIN_TASK_LENGTH, 
    DEBUG_MODE,
    CHAT_MODEL,
    ENABLE_CHAT_VERIFICATION,
    AI_PROVIDER
)

# Import security manager for protecting sensitive data
from plugins import plugin_manager

# Global variables for AI clients
_openai_client = None

def _initialize_openai():
    """Initialize OpenAI client if not already initialized."""
    global _openai_client
    if _openai_client is None and AI_PROVIDER == 'openai':
        from openai import OpenAI
        # Create a custom httpx client without proxies
        http_client = httpx.Client(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
        )
        # Initialize OpenAI client with our custom http client
        _openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        )
    return _openai_client

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def get_ai_response(prompt: str) -> str:
    """Get response from the configured AI provider."""
    from core.openai_client import client
    response = client.chat_completions_create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

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

    # OPTIMIZED: Combined prompt that handles both extraction and context evaluation
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
   - Extract the date when tasks were performed
   - If not explicitly mentioned, use the email/update date
   - Standardize all dates to YYYY-MM-DD format
   - For updates with multiple dates, use the most recent relevant date

7. CATEGORIZATION:
   - Assign each task to a category based on context
   - Use section headers, indentation, or prefix labels to determine categories
   - If a task mentions multiple categories, prefer the most specific one
   - If no category is explicitly mentioned, use "General"

OUTPUT FORMAT:
Return a list of tasks in this exact format:
[
    {{
        "task": "Detailed description of the task",
        "status": "Completed/In Progress/Pending/Blocked",
        "employee": "Full name of the person who did the task",
        "date": "YYYY-MM-DD",
        "category": "Category name",
        "needs_description": true/false,
        "suggested_question": "Specific follow-up question for vague tasks"
    }},
    ...
]

EXAMPLE VAGUE TASKS AND QUESTIONS:
1. Task: "Resume"
   Question: "Could you specify what you did with your resume? (e.g., updated specific sections, created new version, etc.)"
   needs_description: true

2. Task: "VC University"
   Question: "What specific work did you do related to VC University? (e.g., completed specific modules, watched lectures, etc.)"
   needs_description: true

3. Task: "Meeting"
   Question: "What was this meeting about and what were the key outcomes or decisions made?"
   needs_description: true

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
        print(f"Calling {AI_PROVIDER} API for combined extraction and evaluation...")
        try:
            content = get_ai_response(prompt)
        except Exception as e:
            if AI_PROVIDER == 'openai' and "insufficient_quota" in str(e).lower():
                print("OpenAI API quota exceeded. Please check your billing details.")
                return []  # Return empty list instead of raising error
            raise  # Re-raise other errors

        print(f"Received response from {AI_PROVIDER}. Length: {len(content)}")

        # Remove markdown code blocks if present
        if "```" in content:
            print("Removing markdown code blocks...")
            content = re.sub(r'```(?:python|json)?\n(.*?)```', r'\1', content, flags=re.DOTALL)

        content = content.strip()
        print(f"Cleaned content. Now parsing...")

        # Try multiple parsing methods in sequence
        tasks = None

        # Method 1: Direct JSON parsing
        try:
            print("Attempting direct JSON parsing...")
            # Replace single quotes with double quotes and fix boolean values
            json_content = content.replace("'", '"').replace("true", "true").replace("false", "false")
            # Clean up any potential markdown
            json_content = re.sub(r'```(?:json)?\n?(.*?)```', r'\1', json_content, flags=re.DOTALL)
            json_content = json_content.strip()
            tasks = json.loads(json_content)
            print("JSON parsing successful!")
        except json.JSONDecodeError as e:
            print(f"JSON parse failed: {e}")

            # Method 2: Extract array with regex and clean it
            try:
                print("Attempting to extract JSON array with regex...")
                match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
                if match:
                    json_array = match.group(0)
                    # Clean up the JSON array
                    json_array = json_array.replace("'", '"')
                    json_array = json_array.replace("True", "true").replace("False", "false")
                    json_array = re.sub(r'"""', '"', json_array)
                    json_array = re.sub(r'(?<![\[\{,\s])(".*?")\s*(?![\]\},])', r'\1,', json_array)
                    tasks = json.loads(json_array)
                    print("Regex extraction successful!")
                else:
                    print("No JSON array found in content")
            except Exception as e:
                print(f"Regex extraction failed: {e}")

                # Method 3: Fall back to safer eval with preprocessing
                try:
                    print("Attempting eval with ast...")
                    # Replace boolean values and clean up the content
                    eval_content = content.replace("true", "True").replace("false", "False")
                    eval_content = re.sub(r'```(?:python|json)?\n?(.*?)```', r'\1', eval_content, flags=re.DOTALL)
                    eval_content = eval_content.strip()
                    tasks = ast.literal_eval(eval_content)
                    print("AST literal_eval successful!")
                except Exception as e:
                    print(f"AST literal_eval failed: {e}")

                    # Final fallback: Try eval with preprocessing
                    try:
                        print("Last resort: direct eval...")
                        # Replace boolean values and clean up the content
                        eval_content = content.replace("true", "True").replace("false", "False")
                        eval_content = re.sub(r'```(?:python|json)?\n?(.*?)```', r'\1', eval_content, flags=re.DOTALL)
                        eval_content = eval_content.strip()
                        tasks = eval(eval_content)
                        print("Direct eval successful!")
                    except Exception as e:
                        print(f"All parsing methods failed: {e}")
                        raise ValueError("Could not parse AI response as valid task data")

        # Ensure tasks is a list of dictionaries
        if not isinstance(tasks, list):
            print(f"Parsed result is not a list: {type(tasks)}")
            raise ValueError(f"Expected a list of tasks, got {type(tasks)}")

        # Type checking for each task
        valid_tasks = []
        for i, task in enumerate(tasks):
            try:
                if not isinstance(task, dict):
                    print(f"Task {i} is not a dictionary: {type(task)}")
                    continue

                # Ensure all required keys exist
                required_keys = ["task", "status", "employee", "date", "category"]
                if not all(key in task for key in required_keys):
                    missing = [key for key in required_keys if key not in task]
                    print(f"Task {i} missing required keys: {missing}")
                    continue

                # If chat verification is disabled, set default values for missing fields
                if not ENABLE_CHAT_VERIFICATION:
                    if "status" not in task:
                        task["status"] = "Completed"
                    if "category" not in task:
                        task["category"] = "General"
                    if "needs_description" in task:
                        task["needs_description"] = False
                    if "needs_category" in task:
                        task["needs_category"] = False
                    if "needs_status" in task:
                        task["needs_status"] = False

                # Ensure task description has minimum length
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
                        # Default to today's date if parsing fails
                        task["date"] = datetime.now().strftime("%Y-%m-%d")

                # Ensure confidence object exists
                if "confidence" not in task:
                    task["confidence"] = {"category": "MEDIUM", "status": "MEDIUM"}
                
                # Ensure needs_description and suggested_question exist
                if "needs_description" not in task:
                    # Set needs_description based on task length and content
                    task["needs_description"] = (
                        len(task["task"].strip()) < 15 or  # Short tasks
                        task["task"].strip().count(" ") < 2 or  # Few words
                        not any(word in task["task"].lower() for word in ["updated", "completed", "worked", "created", "fixed", "improved"])  # No action verbs
                    )

                if task.get("needs_description") and "suggested_question" not in task:
                    task["suggested_question"] = f"Can you provide more details about what you did for '{task['task']}'?"

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
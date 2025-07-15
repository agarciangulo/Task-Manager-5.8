"""
Task extraction functionality for Task Manager.
Handles extracting structured tasks from freeform text with security protection.
"""
import json
import re
import ast
import traceback
from dateutil import parser
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.config.settings import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    CHAT_MODEL,
    DEBUG_MODE,
    MIN_TASK_LENGTH
)

# Import security manager for protecting sensitive data
from src.plugins import plugin_manager

import httpx
from openai import OpenAI
from src.core.openai_client import client

# Create a custom httpx client without proxies
http_client = httpx.Client(
    base_url="https://api.openai.com/v1",
    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
)

# Initialize OpenAI client with our custom http client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    http_client=http_client
)

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def extract_tasks_from_update(text: str) -> List[Dict[str, Any]]:
    """
    Extract structured tasks from freeform text with improved error handling and security.
    
    Args:
        text: The text to extract tasks from.
        
    Returns:
        List[Dict[str, Any]]: List of task dictionaries.
    """
    if not text or len(text.strip()) < MIN_TASK_LENGTH:
        return []

    print("Starting task extraction...")
    
    # Get the project protection plugin if available
    protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
    
    # Apply protection to the input text if the plugin is available
    protected_text = text
    if protection_plugin and protection_plugin.enabled:
        # Only protect project names that are already known
        # New projects will be discovered during processing and protected afterward
        protected_text = protection_plugin.protect_text(text)

    prompt = f"""You are TaskExtractor, an expert system that extracts structured task updates from complex work logs and emails.

YOUR TASK:
Extract ONLY the actionable tasks from the provided work log, which may contain forwarded emails, email threads, or multiple reports. Follow these precise steps:

1. EMAIL STRUCTURE ANALYSIS:
   - Identify the most recent and relevant activity report in the email thread
   - Recognize different report formats (Hours Breakdown, Planned vs Completed, etc.)
   - Identify the primary author of each section
   - Handle forwarded emails by associating tasks with the correct person

2. SENDER IDENTIFICATION:
   - Extract the full name of the person who performed the tasks (not necessarily the email sender)
   - If multiple people are mentioned, correctly attribute tasks to each person
   - Look for patterns like "From:", email signatures, or introductory lines to identify the task performer

3. TASK EXTRACTION STRATEGIES:
   - Look for explicit "Completed Activities" or "Completed Tasks" sections first
   - Extract from "Planned Activities" only if corresponding completed activities are not found
   - Recognize tasks in bullet points, numbered lists, paragraphs, and project sections
   - Parse tasks across different formatting styles (dashes, asterisk, paragraphs)
   - Identify action verbs to determine what work was performed
   - Ignore email headers, greetings, and signatures that don't contain task information

4. STATUS DETERMINATION - CLASSIFY AS:
   - "Completed": Task explicitly marked as completed or described in past tense
   - "In Progress": Work started but explicitly mentioned as not finished
   - "Pending": Mentioned in "Planned" section but not in "Completed" section
   - "Blocked": Explicitly mentioned as blocked by dependencies or issues

5. DATE EXTRACTION:
   - For each task, extract the date when it was performed
   - If not explicitly mentioned with the task, use the email date
   - Standardize all dates to YYYY-MM-DD format
   - For emails with multiple dates, use the most recent relevant date for each task

6. CATEGORIZATION - CRITICAL RULES:
   - ALWAYS use the specific project name mentioned in the task as the category
   - If a task mentions "Project Alpha", use "Project Alpha" as the category, NOT "Projects" or "Alpha"
   - If a task mentions "Secret Initiative Beta", use "Secret Initiative Beta" as the category
   - Do NOT group tasks under generic categories like "New Projects", "Development", "Meetings"
   - Use the exact project name as it appears in the text
   - If no specific project is mentioned, use "Uncategorized"
   - If a task mentions multiple projects, use the most specific/relevant one mentioned in that task

7. TASK ENHANCEMENT:
   - Ensure each task has a clear action verb
   - Include sufficient context to understand what was accomplished
   - Connect related information to create coherent task descriptions
   - Preserve technical terms, project names, and specific references

IMPORTANT OUTPUT REQUIREMENTS:
- Return ONLY a valid Python list of dictionaries with EXACTLY these keys: "task", "status", "employee", "date", "category"
- Each task description must be clear, specific, and self-contained
- Date format must be YYYY-MM-DD
- Status must be exactly one of: "Completed", "In Progress", "Pending", "Blocked"
- Do not include explanations, markdown, or any text outside the list of task dictionaries

SPECIAL CASES TO HANDLE:
- Handle tasks mentioned in both "Planned" and "Completed" sections by creating only one task entry
- For "Hours Breakdown" sections, extract the categories but don't treat the hours as tasks
- Ignore tasks that are merely attendance at meetings unless specific contributions are mentioned
- When a task spans multiple emails or days, extract it only once with the most recent status

Now extract the tasks from this input: {protected_text}"""

    try:
        print("Calling AI API...")
        if AI_PROVIDER == 'gemini':
            from src.core.gemini_client import client as gemini_client
            response_text = gemini_client.generate_content(prompt, temperature=0.3)
            content = response_text
        elif AI_PROVIDER == 'openai':
            from src.core.openai_client import client as openai_client
            response = openai_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response.choices[0].message.content
        else:
            raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}")

        print(f"Received response from AI. Length: {len(content)}")
        print(f"🔍 DEBUG: AI Response preview: {content[:500]}...")

        # Remove markdown code blocks if present
        if "```" in content:
            print("Removing markdown code blocks...")
            content = re.sub(r'```(?:python|json)?\n(.*?)```', r'\1', content, flags=re.DOTALL)

        content = content.strip()
        print(f"Cleaned content. Now parsing...")
        print(f"🔍 DEBUG: Cleaned content preview: {content[:500]}...")

        # Try multiple parsing methods in sequence
        tasks = None

        # Method 1: Direct JSON parsing
        try:
            print("Attempting direct JSON parsing...")
            # Replace single quotes with double quotes for JSON
            json_content = content.replace("'", '"')
            tasks = json.loads(json_content)
            print("JSON parsing successful!")
        except json.JSONDecodeError as e:
            print(f"JSON parse failed: {e}")

            # Method 2: Extract array with regex
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

                # Method 3: Fall back to safer eval
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
                        print(f"🔍 DEBUG: Full content that failed to parse: {content}")
                        raise ValueError("Could not parse AI response as valid task data")

        # Ensure tasks is a list of dictionaries
        if not isinstance(tasks, list):
            print(f"Parsed result is not a list: {type(tasks)}")
            print(f"🔍 DEBUG: Parsed result: {tasks}")
            raise ValueError(f"Expected a list of tasks, got {type(tasks)}")

        print(f"🔍 DEBUG: Successfully parsed {len(tasks)} raw tasks")

        # Type checking for each task
        valid_tasks = []
        for i, task in enumerate(tasks):
            try:
                if not isinstance(task, dict):
                    print(f"Task {i} is not a dictionary: {type(task)}")
                    print(f"🔍 DEBUG: Task {i} content: {task}")
                    continue

                # Ensure all required keys exist
                required_keys = ["task", "status", "employee", "date", "category"]
                if not all(key in task for key in required_keys):
                    missing = [key for key in required_keys if key not in task]
                    print(f"Task {i} missing keys: {missing}")
                    print(f"🔍 DEBUG: Task {i} content: {task}")
                    continue

                # Ensure task description has minimum length
                if not task["task"] or len(task["task"].strip()) < MIN_TASK_LENGTH:
                    print(f"Task {i} description too short: '{task['task']}'")
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

                valid_tasks.append(task)
                print(f"✅ Task {i+1} validated: {task.get('task', '')[:50]}...")
            except Exception as e:
                print(f"Error validating task {i}: {e}")
                print(f"🔍 DEBUG: Task {i} that caused error: {task}")
                continue

        print(f"Successfully validated {len(valid_tasks)} tasks")
        
        # Unprotect tasks if protection was applied and PRESERVE_TOKENS_IN_UI is False
        if protection_plugin and protection_plugin.enabled and not PRESERVE_TOKENS_IN_UI:
            try:
                # First, process the tasks to add any new project categories to the security manager
                for task in valid_tasks:
                    if 'category' in task and task['category'] and task['category'] != "Uncategorized":
                        # Make sure this category is known to the security manager
                        # This call will create a token mapping if it doesn't exist
                        protection_plugin.security_manager.tokenize_project(task['category'])
                
                # Now unprotect the tasks to restore original project names
                valid_tasks = protection_plugin.unprotect_task_list(valid_tasks)
            except Exception as e:
                print(f"Error unprotecting tasks: {e}")
        
        print(f"🔍 DEBUG: Final result: {len(valid_tasks)} tasks ready for return")
        return valid_tasks

    except Exception as e:
        import traceback
        print(f"Error extracting tasks: {e}")
        print(traceback.format_exc())
        # Return a more informative error that you'll display to the user
        raise ValueError(f"Task extraction failed: {str(e)}\n{traceback.format_exc()}")

def get_ai_response(prompt: str) -> str:
    """Get response from the configured AI provider."""
    response = client.chat_completions_create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

def chunk_email_text(text, max_chunk_size=30):
    """
    Flexibly chunk email text by project/section headers, with fallbacks for unstructured text.
    Args:
        text: The full email text
        max_chunk_size: Max lines per chunk if no headers found
    Returns:
        List of text chunks
    """
    print(f"\n🔪 DEBUG: Starting email chunking...")
    print(f"   Input text length: {len(text)} characters")
    
    # Normalize line endings
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    print(f"   Total lines: {len(lines)}")
    
    chunks = []
    current_chunk = []
    header_pattern = re.compile(r"^(\s*[-*]?\s*[A-Z][A-Za-z0-9 &()'\-]+:)")
    
    print(f"   Scanning for headers...")
    header_count = 0
    
    for i, line in enumerate(lines):
        if header_pattern.match(line):
            header_count += 1
            print(f"     Found header at line {i+1}: {line.strip()}")
            # Start a new chunk if current chunk is not empty
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                chunks.append(chunk_text)
                print(f"     Created chunk {len(chunks)} with {len(current_chunk)} lines ({len(chunk_text)} chars)")
                current_chunk = []
        current_chunk.append(line)
    
    # Add the last chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        chunks.append(chunk_text)
        print(f"     Created final chunk {len(chunks)} with {len(current_chunk)} lines ({len(chunk_text)} chars)")
    
    print(f"   Found {header_count} headers, created {len(chunks)} chunks")
    
    # Fallback: If only one chunk and it's too large, split by max_chunk_size
    if len(chunks) == 1 and len(lines) > max_chunk_size:
        print(f"   ⚠️ Only one chunk created, but text is large ({len(lines)} lines)")
        print(f"   🔄 Applying fallback chunking by {max_chunk_size} lines...")
        
        fallback_chunks = []
        for i in range(0, len(lines), max_chunk_size):
            fallback_chunk = '\n'.join(lines[i:i+max_chunk_size]).strip()
            fallback_chunks.append(fallback_chunk)
            print(f"     Created fallback chunk {len(fallback_chunks)}: lines {i+1}-{min(i+max_chunk_size, len(lines))} ({len(fallback_chunk)} chars)")
        
        print(f"   ✅ Fallback created {len(fallback_chunks)} chunks")
        return fallback_chunks
    
    final_chunks = [c for c in chunks if c]
    print(f"   ✅ Final result: {len(final_chunks)} chunks")
    
    for i, chunk in enumerate(final_chunks):
        print(f"     Chunk {i+1}: {len(chunk)} characters")
    
    return final_chunks
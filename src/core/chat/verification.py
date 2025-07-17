"""
Chat verification for Task Manager.
Handles verification of incomplete task information through conversation.
"""
import re
from typing import Dict, List, Any, Optional, Union
import traceback

from src.core import list_all_categories
from src.core.task_processor import insert_or_update_task

def generate_verification_questions(incomplete_tasks):
    """
    Generate clear verification questions for incomplete tasks.
    
    Args:
        incomplete_tasks: List of tasks with missing information.
        
    Returns:
        str: Message with verification questions.
    """
    verification_message = "I noticed some tasks that could use a bit more detail to make them clearer. Let me ask about each one:\n\n"
    
    for i, task in enumerate(incomplete_tasks, 1):
        # Start with the task description
        verification_message += f"📝 Task {i}: \"{task['task']}\"\n"
        
        # Create a list of what's needed for this task
        needs_list = []
        
        # Ask for more details if needed - use the AI-generated suggested question
        if task.get("needs_description"):
            if task.get("suggested_question") and task["suggested_question"].strip():
                needs_list.append(f"❓ {task['suggested_question']}")
            else:
                # Fallback question if no suggested question was generated
                task_text = task['task'].lower().strip()
                if len(task_text.split()) <= 2:
                    needs_list.append(f"❓ Could you provide more details about '{task['task']}'? What specifically was accomplished?")
                else:
                    needs_list.append("❓ Could you tell me more about what this task involved? What were the specific outcomes?")
        
        # Ask about category if needed
        if task.get("needs_category") or task.get("category") == "General":
            # Get suggested categories
            try:
                # For now, use an empty list since we don't have a specific database context
                suggested_categories = []
                needs_list.append(f"📂 Which project does this belong to?")
            except:
                needs_list.append("📂 Which project does this belong to?")
            
        # Ask about status if needed
        if task.get("needs_status"):
            needs_list.append("📊 What's the current status? (Completed, In Progress, or Pending)")
        
        # Add the needs list as bullet points
        for need in needs_list:
            verification_message += f"{need}\n"
        
        verification_message += "\n"
    
    # Add clear instructions with examples
    verification_message += "You can respond in a natural way. For example:\n\n"
    
    # Generate example response based on actual tasks
    if incomplete_tasks:
        example_task = incomplete_tasks[0]
        example_question = example_task.get('suggested_question', 'Here are more details...')
        verification_message += f"\"For task 1: {example_question} [your answer]. "
        
        if example_task.get("needs_category") or example_task.get("category") == "General":
            verification_message += "It's part of [project name]. "
            
        if example_task.get("needs_status"):
            verification_message += "The status is [completed/in progress/pending].\"\n\n"
    
    verification_message += "Or you can use a more structured format if you prefer:\n"
    verification_message += "1. Details: [your detailed explanation], Category: [project], Status: [status]\n"
    
    return verification_message

def extract_task_info_from_response(task, response_text):
    """
    Use AI to extract task information from freeform text.
    
    Args:
        task: Original task that needs verification
        response_text: User's freeform response about the task
        
    Returns:
        Dict: Updated task information
    """
    from src.core.gemini_client import client, CHAT_MODEL
    
    prompt = f"""You are a task information extractor. Given a vague task and a user's response providing more details, extract the complete task information.

Original task: {task['task']}
User's response: {response_text}

Extract the following information:
1. A clear, detailed task description
2. The appropriate category/project
3. The current status (Completed, In Progress, or Pending)

If any information is missing from the response, use the original task information.

Return the information in this JSON format:
{{
    "description": "Detailed task description",
    "category": "Project/category name",
    "status": "Completed/In Progress/Pending"
}}
"""
    
    try:
        response = client.chat_completions_create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        import json
        # Handle both OpenAI and Gemini response formats
        if hasattr(response, 'choices'):
            # OpenAI format
            content = response.choices[0].message.content
        else:
            # Gemini format (response is already a dict)
            content = response['choices'][0]['message']['content']
        
        # Debug: Print the actual content
        print(f"🔍 DEBUG: Gemini response content: '{content}'")
        print(f"🔍 DEBUG: Content length: {len(content)}")
        
        # Check if content is empty
        if not content or not content.strip():
            print(f"⚠️ Empty response content from Gemini")
            return task
        
        # Extract JSON from markdown code blocks if present
        import re
        json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()
            print(f"🔍 DEBUG: Extracted JSON from markdown: '{content}'")
        
        result = json.loads(content)
        
        # Update the task with the extracted information
        updated_task = task.copy()
        if result.get("description"):
            updated_task["task"] = result["description"]
            updated_task["needs_description"] = False
            
        if result.get("category"):
            updated_task["category"] = result["category"]
            updated_task["needs_category"] = False
            
        if result.get("status"):
            updated_task["status"] = result["status"]
            updated_task["needs_status"] = False
            
        return updated_task
        
    except Exception as e:
        print(f"Error extracting task info: {e}")
        print(f"Full error: {traceback.format_exc()}")  # Add full traceback
        return task

def parse_verification_response(user_response, chat_context):
    """
    Parse the user's response to verification questions.
    
    Args:
        user_response: Text response from the user.
        chat_context: Current chat context with pending tasks.
        
    Returns:
        Dict: Result of parsing the response.
    """
    if "pending_tasks" not in chat_context or not chat_context["pending_tasks"]:
        return {
            "status": "error",
            "message": "I don't have any pending tasks to verify. Please submit new tasks first."
        }
    
    pending_tasks = chat_context["pending_tasks"]
    
    # Parse responses
    updated_tasks = []
    still_pending_tasks = []
    
    # Split response into lines
    lines = user_response.strip().split('\n')
    
    # First try to match responses to tasks using task names and numbers
    current_task = None
    current_response = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try different ways to identify which task this line is about
        task_matched = False
        
        # Method 1: Check for task numbers (e.g., "1." or "Task 1:")
        number_match = re.match(r'^(?:task\s*)?(\d+)[.:]', line.lower())
        if number_match:
            task_index = int(number_match.group(1)) - 1
            if 0 <= task_index < len(pending_tasks):
                # If we were building a response for a previous task, process it
                if current_task is not None and current_response:
                    process_task_response(current_task, ' '.join(current_response), updated_tasks, still_pending_tasks)
                
                current_task = pending_tasks[task_index]
                current_response = [re.sub(r'^(?:task\s*)?(\d+)[.:]', '', line).strip()]
                task_matched = True
                
        # Method 2: Check for task name mentions
        if not task_matched:
            for task in pending_tasks:
                if task["task"].lower() in line.lower():
                    # If we were building a response for a previous task, process it
                    if current_task is not None and current_response:
                        process_task_response(current_task, ' '.join(current_response), updated_tasks, still_pending_tasks)
                    
                    current_task = task
                    current_response = [line]
                    task_matched = True
                    break
        
        # If no task match found, append to current response if we have a current task
        if not task_matched and current_task is not None:
            current_response.append(line)
    
    # Process the last task if we have one
    if current_task is not None and current_response:
        process_task_response(current_task, ' '.join(current_response), updated_tasks, still_pending_tasks)
    
    # If we haven't matched any tasks but have a response, try to match based on content
    if not updated_tasks and not still_pending_tasks and lines:
        # Use the entire response for each pending task and let the AI figure it out
        full_response = ' '.join(lines)
        for task in pending_tasks:
            updated_task = extract_task_info_from_response(task, full_response)
            if (updated_task["task"] != task["task"] or 
                updated_task.get("category") != task.get("category") or 
                updated_task.get("status") != task.get("status")):
                print(f"Task updated from full response: {updated_task['task']}")
                updated_tasks.append(updated_task)
            else:
                still_pending_tasks.append(task)
    
    # If all tasks were updated, return complete status
    if not still_pending_tasks:
        return {
            "status": "complete",
            "message": "All tasks have been verified and updated successfully.",
            "updated_tasks": updated_tasks
        }
    # If some tasks were updated but others still need verification
    elif updated_tasks:
        return {
            "status": "partial",
            "message": "Some tasks were updated, but others still need verification.",
            "follow_up": generate_verification_questions(still_pending_tasks),
            "updated_tasks": updated_tasks,
            "pending_tasks": still_pending_tasks
        }
    # If no tasks were updated
    else:
        return {
            "status": "error",
            "message": "I couldn't understand the updates for any tasks. Please try again with more specific information.",
            "follow_up": generate_verification_questions(pending_tasks)
        }

def process_task_response(task, response_text, updated_tasks, still_pending_tasks):
    """Helper function to process a single task response."""
    updated_task = extract_task_info_from_response(task, response_text)
    if (updated_task["task"] != task["task"] or 
        updated_task.get("category") != task.get("category") or 
        updated_task.get("status") != task.get("status")):
        print(f"Task updated: {updated_task['task']}")
        updated_tasks.append(updated_task)
    else:
        still_pending_tasks.append(task)

def generate_combined_coaching_insights(person_name, processed_tasks, existing_tasks, peer_feedback=None):
    """
    Generate combined coaching insights and task verification in a single API call.
    
    Args:
        person_name: Name of the person to analyze
        processed_tasks: List of processed tasks
        existing_tasks: DataFrame of existing tasks
        peer_feedback: Optional peer feedback data
        
    Returns:
        Dict containing coaching insights and verification status
    """
    from src.core.gemini_client import client, CHAT_MODEL
    
    # Filter recent tasks
    from datetime import datetime, timedelta
    
    recent_tasks = existing_tasks[existing_tasks['date'] >= datetime.now() - timedelta(days=14)]
    
    # Build a combined prompt for coaching insights and verification
    prompt = f"""You are TaskCoach, an AI assistant that provides both coaching insights and task verification.

ANALYZE THE FOLLOWING DATA FOR {person_name}:
1. Current tasks: {processed_tasks}
2. Task history (14 days): {recent_tasks[['task', 'status', 'employee', 'date', 'category']].to_dict(orient='records') if not recent_tasks.empty else []}
3. Peer feedback: {peer_feedback or []}

PERFORM TWO SEPARATE ANALYSES:

PART 1 - COACHING INSIGHTS:
- Task completion rates and patterns
- Work distribution across different projects
- Recent productivity trends
- Task complexity and priority handling
- Collaboration patterns

PART 2 - TASK VERIFICATION:
For each task in the current tasks list, verify if it has complete information:
- Does it have a clear description with enough detail?
- Does it have an appropriate category/project?
- Is the status clear and appropriate?

OUTPUT FORMAT:
Provide your response as a JSON object with the following structure:
{{
  "coaching_insights": "Your coaching insights in a conversational, supportive tone...",
  "tasks_verification": [
    {{
      "task_index": 0,
      "task": "Original task text",
      "is_complete": true/false,
      "missing_fields": ["description", "category", "status"] (if any),
      "suggested_question": "A question to get missing information" (if needed)
    }},
    ...repeat for each task...
  ]
}}

Use personal language like "I notice..." and "You're doing well at..." in the coaching insights.
Keep insights conversational (3-4 sentences per insight) and avoid technical terms.
"""

    try:
        response = client.chat_completions_create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        
        content = response.choices[0].message.content
        
        # Parse the JSON response
        import json
        import re
        
        # Try to extract JSON
        json_match = re.search(r'({.*})', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                return result
            except json.JSONDecodeError:
                pass
        
        # Fallback parsing methods
        try:
            # Clean up potential JSON issues
            cleaned_content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_content)
            return result
        except json.JSONDecodeError:
            # Last resort, return partial data
            return {
                "coaching_insights": "Unable to generate coaching insights at this time.",
                "tasks_verification": []
            }
    except Exception as e:
        print(f"Error generating combined insights: {e}")
        return {
            "coaching_insights": "Unable to generate coaching insights at this time.",
            "tasks_verification": []
        }
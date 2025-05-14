"""
Chat message handler for Task Manager.
Handles processing of chat messages for task verification.
"""
from typing import Dict, Any, Optional
import re
import traceback

from core.task_extractor import extract_tasks_from_update
from core.task_processor import insert_or_update_task, batch_insert_tasks
from core.notion_service import NotionService
from core import fetch_notion_tasks

from core.chat.verification import (
    generate_verification_questions,
    parse_verification_response
)

from core.agents.notion_agent import NotionAgent
from core.agents.task_processing_agent import TaskProcessingAgent

notion_agent = NotionAgent()
task_processing_agent = TaskProcessingAgent()

def is_email_content(message):
    """
    Check if a message appears to be an email or task update.
    
    Args:
        message: Message text to check.
        
    Returns:
        bool: True if the message appears to be an email or task update.
    """
    # Simple heuristic - look for common email patterns
    email_patterns = [
        # From line
        r"From:.*@",
        # Subject line
        r"Subject:",
        # Date line
        r"Date:",
        # Common task report headers
        r"(completed|tasks|updates|progress|status).{0,20}report",
        # Task bullets
        r"(-|\*|\d+\.)\s+(completed|finished|worked on|started|updated)"
    ]
    
    for pattern in email_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return True
            
    # Check if it's long enough to potentially be an email
    if len(message.split()) > 30:  # Arbitrary threshold
        return True
        
    return False

def process_email_tasks(email_content, user_id, chat_context):
    """
    Process tasks from email with verification for incomplete information.
    
    Args:
        email_content: Text content containing tasks.
        user_id: ID of the user.
        chat_context: Chat session context.
        
    Returns:
        Dict: Result of processing.
    """
    # Extract tasks using optimized extraction with integrated context evaluation
    try:
        extracted_tasks = extract_tasks_from_update(email_content)
        
        if not extracted_tasks:
            return {
                "complete_count": 0,
                "incomplete_count": 0,
                "verification_message": "I couldn't find any tasks in your message. Please try again with more details.",
                "status": "no_tasks"
            }
    except Exception as e:
        print(f"Error extracting tasks: {e}")
        print(traceback.format_exc())
        return {
            "complete_count": 0,
            "incomplete_count": 0,
            "verification_message": f"I had trouble understanding your message. Error: {str(e)}",
            "status": "error"
        }
    
    # Normalize dates for all tasks
    for task in extracted_tasks:
        if "date" in task and task["date"]:
            task["date"] = notion_agent.normalize_date_for_notion(task["date"])
    
    # Identify tasks needing verification using the integrated context evaluation
    complete_tasks = []
    incomplete_tasks = []
    processing_log = []  # Track processing results
    
    # Get existing tasks for similarity matching
    existing_tasks = fetch_notion_tasks()
    
    # First pass: Identify which tasks need verification
    for task in extracted_tasks:
        # Check if task needs verification based on the new context flags
        needs_verification = (
            task.get("needs_description", False) or 
            task.get("needs_category", False) or 
            task.get("category") == "Needs Context" or
            task.get("needs_status", False) or
            task.get("confidence", {}).get("category") == "LOW" or
            task.get("confidence", {}).get("status") == "LOW" or
            len(task.get("task", "").strip()) < 15  # Additional check for short tasks
        )
        
        if needs_verification:
            incomplete_tasks.append(task)
            processing_log.append(f"Task '{task['task']}' needs verification")
        else:
            complete_tasks.append(task)
    
    # If we have any incomplete tasks, don't process any tasks yet
    if incomplete_tasks:
        chat_context["pending_tasks"] = incomplete_tasks
        chat_context["complete_tasks"] = complete_tasks  # Store complete tasks for later
        verification_message = generate_verification_questions(incomplete_tasks)
        
        # Store processing logs in context
        chat_context["processing_logs"] = processing_log
        
        return {
            "complete_count": len(complete_tasks),
            "incomplete_count": len(incomplete_tasks),
            "verification_message": verification_message,
            "logs": processing_log,
            "status": "verification_needed"
        }
    
    # If all tasks are complete, process them
    for task in complete_tasks:
        try:
            task_log = []
            success, result = task_processing_agent.process_task(task, existing_tasks, task_log)
            processing_log.extend(task_log)
            
            if success:
                processing_log.append(f"Task '{task['task']}' processed successfully")
            else:
                processing_log.append(f"Task '{task['task']}' failed to process: {result}")
        except Exception as e:
            processing_log.append(f"Error processing task '{task['task']}': {e}")
            print(f"Error processing task: {e}")
            print(traceback.format_exc())
    
    # Store processing logs and complete tasks in context
    chat_context["processing_logs"] = processing_log
    chat_context["processed_tasks"] = complete_tasks
    
    return {
        "complete_count": len(complete_tasks),
        "incomplete_count": 0,
        "verification_message": "All tasks were processed successfully.",
        "logs": processing_log,
        "status": "complete"
    }

def process_regular_chat(message, user_id, chat_context):
    """
    Process a regular chat message (not an email or verification response).
    
    Args:
        message: Message text.
        user_id: ID of the user.
        chat_context: Chat session context.
        
    Returns:
        str: Response message.
    """
    # This is where you would integrate with a chatbot/LLM for general chat
    # Simple implementation for now
    if "help" in message.lower():
        return ("I can help you manage your tasks. You can paste an email or update with tasks, "
                "and I'll extract and organize them. If I need more information about a task, "
                "I'll ask for clarification.")
    elif "list" in message.lower() and "categories" in message.lower():
        from core import list_all_categories
        categories = list_all_categories()
        return f"Here are the available categories: {', '.join(categories)}"
    else:
        return ("I'm here to help with task management. You can send me an email or update "
                "with your tasks, and I'll process them for you. Type 'help' for more information.")

def handle_chat_message(message, user_id, chat_context):
    """
    Handle incoming chat messages with optimized API calls.
    
    Args:
        message: Message text.
        user_id: ID of the user.
        chat_context: Chat session context.
        
    Returns:
        dict or str: Response data or message.
    """
    try:
        # Special command to get final results for display
        if message == "get_final_results" and "processed_tasks" in chat_context:
            try:
                # OPTIMIZATION: Use combined coaching insights function
                from core import fetch_notion_tasks, fetch_peer_feedback
                
                # Get person name from the first task
                person_name = ""
                if chat_context["processed_tasks"] and isinstance(chat_context["processed_tasks"][0], dict):
                    person_name = chat_context["processed_tasks"][0].get("employee", "")
                    
                # Get existing tasks
                existing_tasks = fetch_notion_tasks()
                    
                # Get peer feedback
                peer_feedback = []
                if person_name:
                    try:
                        peer_feedback = fetch_peer_feedback(person_name)
                    except Exception as e:
                        print(f"Error fetching peer feedback: {e}")
                
                # OPTIMIZATION: Generate combined insights
                from core.chat.verification import generate_combined_coaching_insights
                combined_results = generate_combined_coaching_insights(
                    person_name,
                    chat_context["processed_tasks"],
                    existing_tasks,
                    peer_feedback
                )
                
                # Extract coaching insights
                coaching = combined_results.get("coaching_insights", 
                    "Unable to generate coaching insights at this time.")
                
                # Format tasks for display
                tasks_formatted = []
                for task in chat_context["processed_tasks"]:
                    if isinstance(task, dict) and "task" in task and "status" in task:
                        tasks_formatted.append({
                            'task': task['task'],
                            'status': task['status'],
                            'employee': task.get('employee', ''),
                            'category': task.get('category', '')
                        })
                        
                return {
                    "status": "complete",
                    "processed_tasks": tasks_formatted,
                    "coaching": coaching,
                    "logs": chat_context.get("processing_logs", [])
                }
            except Exception as e:
                print(f"Error generating final results: {e}")
                print(traceback.format_exc())
                return {
                    "status": "error",
                    "message": f"Error generating final results: {str(e)}"
                }
          
        # Check if we're in the middle of a verification flow
        if "pending_tasks" in chat_context and chat_context["pending_tasks"]:
            # Process verification response
            result = parse_verification_response(message, chat_context)
            
            if result["status"] == "complete":
                # All tasks verified and processed - now explicitly process all tasks
                try:
                    from core import fetch_notion_tasks, fetch_peer_feedback
                    from core.openai_client import get_coaching_insight
                    from core.task_processor import insert_or_update_task, batch_insert_tasks  # Import batch_insert_tasks
                    from datetime import datetime, timedelta
                    import pandas as pd

                    # Get existing tasks from Notion
                    existing_tasks = fetch_notion_tasks()
                    
                    # Merge complete tasks with newly verified tasks
                    all_tasks = []
                    
                    # First add the original complete tasks
                    complete_tasks = chat_context.get("complete_tasks", [])
                    all_tasks.extend(complete_tasks)
                    
                    # Then add the verified tasks with their updated information
                    verified_tasks = result.get("updated_tasks", [])  # Get the updated tasks from verification result
                    
                    # For each verified task, preserve the original date and employee
                    for i, verified_task in enumerate(verified_tasks):
                        # Get the original task from pending_tasks
                        original_task = chat_context["pending_tasks"][i]
                        # Preserve the original date and employee
                        verified_task["date"] = original_task.get("date", datetime.now().strftime("%Y-%m-%d"))
                        verified_task["employee"] = original_task.get("employee", "")
                    
                    all_tasks.extend(verified_tasks)
                    
                    # Store all tasks in context for future reference
                    chat_context["processed_tasks"] = all_tasks
                    
                    log_output = []
                    
                    # Use batch insert to process all tasks together
                    batch_result = batch_insert_tasks(all_tasks, existing_tasks)
                    
                    if batch_result["status"] == "complete":
                        for log_msg in batch_result["results"]:
                            log_output.append(f"✅ {log_msg}")
                    else:
                        log_output.append("❌ Error processing tasks in batch")
                    
                    # Get person name from the first task
                    person_name = ""
                    if all_tasks and isinstance(all_tasks[0], dict):
                        person_name = all_tasks[0].get("employee", "")
                        
                    # Get recent tasks for coaching insights
                    recent_tasks = pd.DataFrame()
                    try:
                        recent_tasks = existing_tasks[existing_tasks['date'] >= datetime.now() - timedelta(days=14)]
                        print(f"Retrieved {len(recent_tasks)} recent tasks for analysis")
                    except Exception as e:
                        print(f"Error retrieving recent tasks: {e}")
                        
                    # Get peer feedback
                    peer_feedback = []
                    if person_name:
                        try:
                            peer_feedback = fetch_peer_feedback(person_name)
                        except Exception as e:
                            print(f"Error fetching peer feedback: {e}")
                            
                    # Generate coaching insights
                    print("Generating coaching insights...")
                    coaching = get_coaching_insight(person_name, all_tasks, recent_tasks, peer_feedback)
                    print("Generated coaching insights")
                    
                    # Format tasks for display
                    tasks_formatted = []
                    for task in all_tasks:
                        if isinstance(task, dict) and "task" in task and "status" in task:
                            tasks_formatted.append({
                                'task': task['task'],
                                'status': task['status'],
                                'employee': task.get('employee', ''),
                                'category': task.get('category', '')
                            })
                    
                    # Return to chat a simple completion message, but include data for results box
                    return {
                        "message": result.get("message", "All tasks have been verified and updated successfully."),
                        "status": "complete",
                        "has_pending_tasks": False,
                        "processed_tasks": tasks_formatted,
                        "coaching": coaching,
                        "logs": log_output + chat_context.get("processing_logs", [])
                    }
                    
                except Exception as e:
                    print(f"Error generating final results: {e}")
                    print(traceback.format_exc())
                    return {
                        "message": result.get("message", "Tasks were verified but there was an error in processing."),
                        "status": "complete",
                        "has_pending_tasks": False
                    }
            elif result["status"] == "partial":
                # Some tasks still need verification
                return {
                    "message": result["message"],
                    "follow_up": result["follow_up"],
                    "has_pending_tasks": True
                }
            else:
                # Error or other status - result might be a string
                if isinstance(result, dict):
                    return result["message"]
                else:
                    return str(result)
        
        # Check if message contains an email to process
        elif is_email_content(message):
            # Process as email with tasks
            result = process_email_tasks(message, user_id, chat_context)
            
            if result["status"] == "verification_needed":
                return f"I've processed {result['complete_count']} tasks that had all the needed information.\n\n" + result["verification_message"]
            elif result["status"] == "complete":
                return f"I've processed all {result['complete_count']} tasks successfully."
            elif result["status"] == "no_tasks":
                return result["verification_message"]
            else:
                return f"Error processing tasks: {result['verification_message']}"
        
        # Handle other types of messages
        else:
            # Regular chat message processing
            return process_regular_chat(message, user_id, chat_context)
    except Exception as e:
        print(f"Error handling chat message: {e}")
        print(traceback.format_exc())
        return "I encountered an error processing your message. Please try again or contact support."
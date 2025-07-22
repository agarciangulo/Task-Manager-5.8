"""
Chat message handler for Task Manager.
Handles processing of chat messages for task verification.
"""
from typing import Dict, Any, Optional
import re
import traceback

from src.core.task_extractor import extract_tasks_from_update
from src.core.task_processor import insert_or_update_task, batch_insert_tasks
from src.core.notion_service import NotionService
from src.core import fetch_notion_tasks

from src.core.chat.verification import (
    generate_verification_questions,
    parse_verification_response
)

from src.core.agents.notion_agent import NotionAgent
from src.core.agents.task_processing_agent import TaskProcessingAgent

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

def process_email_tasks(email_content, user_id, chat_context, database_id: str):
    """
    Process tasks from email with verification for incomplete information.
    
    Args:
        email_content: Text content containing tasks.
        user_id: ID of the user.
        chat_context: Chat session context.
        database_id: The user's task database ID.
        
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
            # Use a local NotionService instance for date normalization
            notion_service = NotionService()
            task["date"] = notion_service.normalize_date_for_notion(task["date"])
    
    # Identify tasks needing verification using the integrated context evaluation
    complete_tasks = []
    incomplete_tasks = []
    processing_log = []  # Track processing results
    
    # Get existing tasks for similarity matching from user's database
    existing_tasks = fetch_notion_tasks(database_id=database_id)
    
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
            success, result = insert_or_update_task(
                database_id=database_id,
                task=task, 
                existing_tasks=existing_tasks, 
                log_output=task_log
            )
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

def process_regular_chat(message, user_id, chat_context, database_id: str):
    """
    Process a regular chat message (not an email or verification response).
    
    Args:
        message: Message text.
        user_id: ID of the user.
        chat_context: Chat session context.
        database_id: The user's task database ID.
        
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
        categories = list_all_categories(database_id=database_id)
        return f"Here are the available categories: {', '.join(categories)}"
    else:
        return ("I'm here to help with task management. You can send me an email or update "
                "with your tasks, and I'll process them for you. Type 'help' for more information.")

def handle_rag_query(message, user_id, chat_context, database_id: str):
    """
    Handle RAG queries using the /ask command.
    
    Args:
        message: The chat message containing the /ask command
        user_id: ID of the user sending the message
        chat_context: Chat session context
        database_id: The user's task database ID
        
    Returns:
        Dict: Response with RAG-generated answer
    """
    try:
        # Extract the actual question from the /ask command
        question = message.strip()[4:].strip()  # Remove '/ask' and whitespace
        
        if not question:
            return {
                "message": "Please provide a question after /ask. For example: /ask How do I handle a client complaint?",
                "type": "error"
            }
        
        # Initialize knowledge base and query guidelines
        from src.core.knowledge.knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(name="guidelines")
        retrieved_chunks = kb.query_guidelines(question, top_k=4)
        
        if not retrieved_chunks:
            return {
                "message": "I couldn't find relevant information in our guidelines for your question. Please try rephrasing or ask about a different topic.",
                "type": "no_results"
            }
        
        # Construct the context string
        context_string = "\n\n---\n\n".join(retrieved_chunks)
        
        # Create the RAG prompt
        prompt = f"""You are PrismaBot, an expert AI assistant for our consultants. Your tone should be helpful, professional, and authoritative. Answer the user's question based *only* on the following context provided from our internal field guides and runbooks. If the context does not contain the answer, you must state that the information is not available in your knowledge base.

CONTEXT:
{context_string}

QUESTION:
{question}

ANSWER:
"""
        
        # Get AI response using the existing AI client
        from src.core.ai_client import call_ai_api
        
        response = call_ai_api(prompt)
        
        if not response:
            return {
                "message": "I'm having trouble generating a response right now. Please try again later.",
                "type": "error"
            }
        
        return {
            "message": response,
            "type": "rag_response",
            "context_sources": len(retrieved_chunks),
            "question": question
        }
        
    except Exception as e:
        print(f"Error in RAG query: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "message": f"I encountered an error while searching our guidelines: {str(e)}. Please try again.",
            "type": "error"
        }

def handle_chat_message(message, user_id, chat_context, database_id: str):
    """
    Main chat message handler.
    
    Args:
        message: The chat message to process.
        user_id: ID of the user sending the message.
        chat_context: Chat session context for maintaining state.
        database_id: The user's task database ID.
        
    Returns:
        Dict: Response with message and any additional data.
    """
    try:
        # Check for /ask command for RAG queries
        if message.strip().startswith('/ask'):
            return handle_rag_query(message, user_id, chat_context, database_id)
        
        # Check if this is a verification response
        if chat_context.get("pending_tasks"):
            # Process verification response
            result = parse_verification_response(message, chat_context["pending_tasks"])
            
            if result["status"] == "complete":
                # All tasks verified, process them
                complete_tasks = chat_context.get("complete_tasks", [])
                all_tasks = complete_tasks + result["verified_tasks"]
                
                # Get existing tasks for similarity matching
                existing_tasks = fetch_notion_tasks(database_id=database_id)
                
                # Process all tasks
                processing_log = []
                for task in all_tasks:
                    try:
                        task_log = []
                        success, result_msg = insert_or_update_task(
                            database_id=database_id,
                            task=task, 
                            existing_tasks=existing_tasks, 
                            log_output=task_log
                        )
                        processing_log.extend(task_log)
                        
                        if success:
                            processing_log.append(f"Task '{task['task']}' processed successfully")
                        else:
                            processing_log.append(f"Task '{task['task']}' failed to process: {result_msg}")
                    except Exception as e:
                        processing_log.append(f"Error processing task '{task['task']}': {e}")
                        print(f"Error processing task: {e}")
                        print(traceback.format_exc())
                
                # Clear pending tasks
                chat_context.pop("pending_tasks", None)
                chat_context.pop("complete_tasks", None)
                chat_context["processing_logs"] = processing_log
                chat_context["processed_tasks"] = all_tasks
                
                return {
                    "message": f"All {len(all_tasks)} tasks have been processed successfully!",
                    "logs": processing_log,
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
            result = process_email_tasks(message, user_id, chat_context, database_id)
            
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
            return process_regular_chat(message, user_id, chat_context, database_id)
    except Exception as e:
        print(f"Error handling chat message: {e}")
        print(traceback.format_exc())
        return "I encountered an error processing your message. Please try again or contact support."
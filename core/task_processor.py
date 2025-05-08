"""
Task processing functionality for Task Manager.
Handles task similarity matching and processing for Notion integration.
"""
import os
import sys
import json
import platform
import subprocess
import urllib.request
import tempfile
from typing import List, Dict, Any, Optional, Union
import numpy as np
import traceback
import re
from datetime import datetime, timedelta
from dateutil import parser
from sklearn.metrics.pairwise import cosine_similarity

from config import (
    DEBUG_MODE, 
    SIMILARITY_THRESHOLD, 
    MIN_TASK_LENGTH,
    ENABLE_TASK_VALIDATION,
    ENABLE_CHAT_VERIFICATION,
    DAYS_THRESHOLD
)
from core.embeddings import (
    get_embedding,
    get_batch_embeddings
)
from core.notion_client import (
    Client as NotionClient,
    insert_task_to_notion,
    update_task_in_notion,
    normalize_date_for_notion
)
from core.task_similarity import check_task_similarity
from plugins import plugin_manager

def debug_print(message):
    """Print debug messages if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(message)

def classify_task_type(task):
    """Classify task into different types for specialized handling."""
    # Use the is_recurring field if available
    if "is_recurring" in task and task["is_recurring"]:
        return "recurring"
        
    task_lower = task["task"].lower()

    # Training/class pattern
    if any(keyword in task_lower for keyword in ["class", "training", "certification", "learning"]):
        return "training"

    # Meeting/attendance pattern
    if any(keyword in task_lower for keyword in ["attended", "meeting", "call", "sync", "session"]):
        return "meeting"

    # Recurring task pattern 
    if any(keyword in task_lower for keyword in ["weekly", "daily", "monthly", "recurring"]):
        return "recurring"

    # Admin task pattern
    if task["category"].lower() == "admin":
        return "admin"

    # Default: regular task
    return "regular"

def insert_or_update_task(task, existing_tasks, log_output=None, batch_mode=False):
    """
    Insert a new task or update existing similar task with intelligent matching.
    
    Args:
        task: The task to process
        existing_tasks: Existing tasks to check against (DataFrame or list)
        log_output: List to append log messages to
        batch_mode: If True, only verify but don't insert to Notion
    """
    # Initialize log_output if not provided
    if log_output is None:
        log_output = []
        
    # Only skip empty tasks, not short ones
    if not task["task"] or not task["task"].strip():
        log_output.append(f"⚠️ Skipping empty task")
        return False, "Task is empty"

    try:
        # Convert DataFrame to list of dictionaries if needed
        if hasattr(existing_tasks, 'to_dict'):
            existing_tasks = existing_tasks.to_dict('records')
        
        # Normalize the date in the task to use current year
        if "date" in task and task["date"]:
            task["date"] = normalize_date_for_notion(task["date"])
        
        log_output.append(f"📋 Processing task: '{task['task']}'")
        log_output.append(f"📅 Task date: {task['date']}")
        
        # Check for task verification needs using the integrated context evaluation
        needs_verification = False
        verification_fields = []
        
        # Check for description needs
        if task.get("needs_description", False):
            needs_verification = True
            verification_fields.append("description")
            log_output.append(f"⚠️ Task needs more detailed description")
            
        # Check category confidence
        if task.get("category") == "Needs Context" or task.get("confidence", {}).get("category") == "LOW":
            needs_verification = True
            task["needs_category"] = True
            verification_fields.append("category")
            log_output.append(f"⚠️ Task needs category verification")
            
        # If verification is needed and we're not in batch mode, return early
        if needs_verification and not batch_mode:
            return False, "Task needs verification"
            
        # Check for similar existing tasks using the hybrid approach
        similarity_result = check_task_similarity(task, existing_tasks)
        
        if similarity_result["is_match"]:
            matched_task = similarity_result["matched_task"]
            log_output.append(f"🔍 Found matching task: '{matched_task['task']}'")
            log_output.append(f"💡 Confidence: {similarity_result['confidence']:.2f}")
            log_output.append(f"📝 {similarity_result['explanation']}")
            
            # Preserve original date and employee from matched task
            task["date"] = matched_task.get("date", task["date"])
            task["employee"] = matched_task.get("employee", task["employee"])
            
            # Update the existing task
            if not batch_mode:
                success, message = update_task_in_notion(matched_task["id"], task)
                if success:
                    log_output.append(f"✅ Updated existing task: {task['task']}")
                else:
                    log_output.append(f"❌ Failed to update task: {message}")
                return success, message
            return True, "Task verified for update"
            
        else:
            log_output.append("🆕 No matching task found, creating new task")
            
            # Create new task
            if not batch_mode:
                success, message = insert_task_to_notion(task)
                if success:
                    log_output.append(f"✅ Created new task: {task['task']}")
                else:
                    log_output.append(f"❌ Failed to create task: {message}")
                return success, message
            return True, "Task verified for creation"
            
    except Exception as e:
        error_msg = f"❌ Error in task processing: {e}"
        log_output.append(error_msg)
        print(error_msg)
        print(traceback.format_exc())
        return False, error_msg

def batch_insert_tasks(tasks, existing_tasks):
    """
    Process multiple tasks efficiently in batch.
    
    Args:
        tasks: List of tasks to process
        existing_tasks: Existing tasks to check against
        
    Returns:
        Dict with processing results
    """
    results = []
    processed_tasks = []
    
    try:
        # First pass: Verify all tasks
        for task in tasks:
            log_output = []
            success, message = insert_or_update_task(task, existing_tasks, log_output, batch_mode=True)
            
            if success:
                processed_tasks.append(task)
                results.extend(log_output)
            else:
                results.append(f"❌ Task verification failed: {message}")
                
        # Second pass: Actually insert/update tasks
        for task in processed_tasks:
            log_output = []
            success, message = insert_or_update_task(task, existing_tasks, log_output)
            results.extend(log_output)
            
        return {
            "status": "complete",
            "results": results
        }
        
    except Exception as e:
        error_msg = f"❌ Error in batch processing: {e}"
        print(error_msg)
        print(traceback.format_exc())
        return {
            "status": "error",
            "results": [error_msg]
        }
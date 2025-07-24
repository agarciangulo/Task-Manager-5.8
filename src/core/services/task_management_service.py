"""
Task Management Service for AI Team Support.
Implements the ITaskService interface with comprehensive business logic.
"""
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta

from src.core.interfaces.task_service import ITaskService
from src.core.exceptions.service_exceptions import (
    TaskServiceError, TaskExtractionError, TaskProcessingError, 
    TaskValidationError, UserNotFoundError, NotionConnectionError
)
from src.core.logging.service_logger import LoggingMixin, log_operation
from src.core.agents.notion_agent import NotionAgent
from src.core.agents.task_extraction_agent import TaskExtractionAgent
from src.core.agents.task_processing_agent import TaskProcessingAgent
from src.core.ai.insights import get_coaching_insight
from core import identify_stale_tasks, list_all_categories
from src.core.services.auth_service import AuthService
from plugins import plugin_manager


class TaskManagementService(ITaskService, LoggingMixin):
    """Service for managing task-related operations."""
    
    def __init__(self, notion_token: str, auth_service: AuthService):
        super().__init__()
        self.notion_token = notion_token
        self.auth_service = auth_service
        self.notion_agent = NotionAgent()
        self.task_extractor = TaskExtractionAgent()
        self.task_processor = TaskProcessingAgent()
    
    @log_operation("extract_tasks_from_text")
    def extract_tasks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract tasks from freeform text."""
        try:
            if not text or not text.strip():
                raise TaskValidationError("Text input is empty or invalid")
            
            self.log_info("extract_tasks_start", text_length=len(text))
            
            # Extract tasks using the agent
            extracted_tasks = self.task_extractor.extract_tasks(text)
            
            self.log_info("extract_tasks_success", 
                         tasks_count=len(extracted_tasks),
                         text_length=len(text))
            
            return extracted_tasks
            
        except Exception as e:
            self.log_error("extract_tasks_error", e, text_length=len(text))
            if isinstance(e, TaskValidationError):
                raise
            raise TaskExtractionError(f"Failed to extract tasks: {str(e)}")
    
    @log_operation("process_user_update")
    def process_user_update(self, text: str, user_id: str) -> Dict[str, Any]:
        """Process a user's text update and return comprehensive results."""
        try:
            # Validate inputs
            if not text or not text.strip():
                raise TaskValidationError("Text input is empty or invalid")
            
            if not user_id:
                raise TaskValidationError("User ID is required")
            
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise TaskServiceError("User does not have a task database configured")
            
            self.log_info("process_update_start", 
                         user_id=user_id,
                         text_length=len(text))
            
            # Step 1: Extract tasks from text
            extracted_tasks = self.extract_tasks_from_text(text)
            
            if not extracted_tasks:
                return {
                    "success": True,
                    "message": "No tasks found in the provided text",
                    "processed_tasks": [],
                    "insights": "",
                    "summary": {
                        "total_tasks": 0,
                        "successful_tasks": 0,
                        "failed_tasks": 0
                    }
                }
            
            # Step 2: Get existing tasks for similarity checking
            existing_tasks = self.notion_agent.fetch_tasks(user.task_database_id)
            
            # Step 3: Process each extracted task
            processed_tasks = []
            successful_tasks = 0
            failed_tasks = 0
            log_output = []
            
            for i, task in enumerate(extracted_tasks):
                try:
                    success, message = self.task_processor.process_task(
                        database_id=user.task_database_id,
                        task=task,
                        existing_tasks=existing_tasks,
                        log_output=log_output
                    )
                    
                    if success:
                        processed_tasks.append({
                            "task": task.get('task', ''),
                            "status": task.get('status', 'Not Started'),
                            "employee": task.get('employee', ''),
                            "category": task.get('category', ''),
                            "priority": task.get('priority', 'Medium'),
                            "date": task.get('date', '')
                        })
                        successful_tasks += 1
                        self.log_info("task_processed_success", 
                                     task_index=i,
                                     task_title=task.get('task', '')[:50])
                    else:
                        failed_tasks += 1
                        self.log_warning("task_processed_failed", 
                                        task_index=i,
                                        error_message=message)
                        
                except Exception as e:
                    failed_tasks += 1
                    self.log_error("task_processed_error", e, task_index=i)
            
            # Step 4: Generate insights
            insights = ""
            try:
                if processed_tasks and not existing_tasks.empty:
                    insights = get_coaching_insight(
                        user.full_name or "User",
                        processed_tasks,
                        existing_tasks,
                        []
                    )
                    self.log_info("insights_generated", insights_length=len(insights))
            except Exception as e:
                self.log_error("insights_generation_error", e)
                insights = "Unable to generate insights at this time."
            
            # Step 5: Create summary
            summary = {
                "total_tasks": len(extracted_tasks),
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": successful_tasks / len(extracted_tasks) if extracted_tasks else 0
            }
            
            self.log_info("process_update_success", 
                         user_id=user_id,
                         total_tasks=len(extracted_tasks),
                         successful_tasks=successful_tasks,
                         failed_tasks=failed_tasks)
            
            return {
                "success": True,
                "message": f"Successfully processed {successful_tasks} out of {len(extracted_tasks)} tasks",
                "processed_tasks": processed_tasks,
                "insights": insights,
                "summary": summary,
                "log": log_output
            }
            
        except Exception as e:
            self.log_error("process_update_error", e, user_id=user_id)
            if isinstance(e, (TaskValidationError, UserNotFoundError, TaskServiceError)):
                raise
            raise TaskServiceError(f"Failed to process user update: {str(e)}")
    
    @log_operation("get_user_tasks")
    def get_user_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a user."""
        try:
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise TaskServiceError("User does not have a task database configured")
            
            # Fetch tasks from Notion
            tasks_df = self.notion_agent.fetch_tasks(user.task_database_id)
            
            if tasks_df.empty:
                return []
            
            # Convert to list of dictionaries
            tasks_list = tasks_df.to_dict('records')
            
            self.log_info("get_user_tasks_success", 
                         user_id=user_id,
                         tasks_count=len(tasks_list))
            
            return tasks_list
            
        except Exception as e:
            self.log_error("get_user_tasks_error", e, user_id=user_id)
            if isinstance(e, (UserNotFoundError, TaskServiceError)):
                raise
            raise TaskServiceError(f"Failed to get user tasks: {str(e)}")
    
    @log_operation("create_task")
    def create_task(self, user_id: str, task_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Create a new task for a user."""
        try:
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise TaskServiceError("User does not have a task database configured")
            
            # Validate task data
            if not task_data.get('task'):
                raise TaskValidationError("Task content is required")
            
            # Insert task into Notion
            success, message = self.notion_agent.insert_task(
                database_id=user.task_database_id,
                task=task_data
            )
            
            if success:
                self.log_info("create_task_success", 
                             user_id=user_id,
                             task_title=task_data.get('task', '')[:50])
                
                # Schedule activity recognition in the background
                try:
                    from src.core.tasks.activity_tasks import recognize_activity_for_task
                    
                    # Extract task ID from the response if available
                    task_id = task_data.get('id') or 'unknown'
                    task_title = task_data.get('task', '')
                    
                    # Schedule the activity recognition task
                    recognize_activity_for_task.delay(user_id, task_id, task_title)
                    
                    self.log_info("activity_recognition_scheduled", 
                                 user_id=user_id,
                                 task_id=task_id)
                    
                except Exception as e:
                    # Don't fail the main task creation if activity recognition fails
                    self.log_error("activity_recognition_scheduling_failed", 
                                  e, user_id=user_id)
            else:
                self.log_error("create_task_failed", 
                              Exception(message), 
                              user_id=user_id)
            
            return success, message
            
        except Exception as e:
            self.log_error("create_task_error", e, user_id=user_id)
            if isinstance(e, (UserNotFoundError, TaskServiceError, TaskValidationError)):
                raise
            raise TaskServiceError(f"Failed to create task: {str(e)}")
    
    @log_operation("update_task")
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update an existing task."""
        try:
            # Update task in Notion
            success, message = self.notion_agent.update_task(
                task_id=task_id,
                task=task_data
            )
            
            if success:
                self.log_info("update_task_success", task_id=task_id)
            else:
                self.log_error("update_task_failed", 
                              Exception(message), 
                              task_id=task_id)
            
            return success, message
            
        except Exception as e:
            self.log_error("update_task_error", e, task_id=task_id)
            raise TaskServiceError(f"Failed to update task: {str(e)}")
    
    @log_operation("delete_task")
    def delete_task(self, task_id: str) -> Tuple[bool, str]:
        """Delete (archive) a task."""
        try:
            # Archive task in Notion
            success, message = self.notion_agent.update_task(
                task_id=task_id,
                task={"archived": True}
            )
            
            if success:
                self.log_info("delete_task_success", task_id=task_id)
            else:
                self.log_error("delete_task_failed", 
                              Exception(message), 
                              task_id=task_id)
            
            return success, message
            
        except Exception as e:
            self.log_error("delete_task_error", e, task_id=task_id)
            raise TaskServiceError(f"Failed to delete task: {str(e)}")
    
    @log_operation("get_tasks_by_category")
    def get_tasks_by_category(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get tasks grouped by category for a user."""
        try:
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise TaskServiceError("User does not have a task database configured")
            
            # Fetch tasks from Notion
            tasks_df = self.notion_agent.fetch_tasks(user.task_database_id)
            
            if tasks_df.empty:
                return {}
            
            # Group by category
            tasks_by_category = {}
            for _, task in tasks_df.iterrows():
                category = task.get('category', 'Uncategorized')
                if category not in tasks_by_category:
                    tasks_by_category[category] = []
                tasks_by_category[category].append(task.to_dict())
            
            self.log_info("get_tasks_by_category_success", 
                         user_id=user_id,
                         categories_count=len(tasks_by_category))
            
            return tasks_by_category
            
        except Exception as e:
            self.log_error("get_tasks_by_category_error", e, user_id=user_id)
            if isinstance(e, (UserNotFoundError, TaskServiceError)):
                raise
            raise TaskServiceError(f"Failed to get tasks by category: {str(e)}")
    
    @log_operation("get_stale_tasks")
    def get_stale_tasks(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get stale tasks for a user."""
        try:
            # Get user information
            user = self.auth_service.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            if not user.task_database_id:
                raise TaskServiceError("User does not have a task database configured")
            
            # Get stale tasks
            stale_tasks = identify_stale_tasks(user.task_database_id, days)
            
            self.log_info("get_stale_tasks_success", 
                         user_id=user_id,
                         days=days,
                         stale_tasks_count=len(stale_tasks))
            
            return stale_tasks
            
        except Exception as e:
            self.log_error("get_stale_tasks_error", e, user_id=user_id, days=days)
            if isinstance(e, (UserNotFoundError, TaskServiceError)):
                raise
            raise TaskServiceError(f"Failed to get stale tasks: {str(e)}") 
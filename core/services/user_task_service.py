"""
Service for managing user-specific task databases in Notion.
"""
import uuid
from typing import Optional, Dict, Any, List
from notion_client import Client
from datetime import datetime

from core.models.user import User
from core.logging_config import get_logger

logger = get_logger(__name__)


class UserTaskService:
    """Service for managing user-specific task databases."""
    
    def __init__(self, notion_token: str):
        """
        Initialize the user task service.
        
        Args:
            notion_token: Notion API token.
        """
        self.notion_client = Client(auth=notion_token)
    
    def create_user_task_database(self, user: User, parent_page_id: str) -> str:
        """
        Create a new task database for a user.
        
        Args:
            user: The user object.
            parent_page_id: The Notion page ID where the database should be created.
            
        Returns:
            str: The database ID of the created task database.
        """
        try:
            # Create database with standard task schema matching master system
            database = self.notion_client.databases.create(
                parent={"page_id": parent_page_id},
                title=[
                    {
                        "type": "text",
                        "text": {
                            "content": f"Tasks - {user.full_name}"
                        }
                    }
                ],
                properties={
                    "Task": {
                        "title": {}
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "Not Started", "color": "gray"},
                                {"name": "In Progress", "color": "blue"},
                                {"name": "Completed", "color": "green"},
                                {"name": "On Hold", "color": "yellow"}
                            ]
                        }
                    },
                    "Priority": {
                        "select": {
                            "options": [
                                {"name": "Low", "color": "gray"},
                                {"name": "Medium", "color": "yellow"},
                                {"name": "High", "color": "red"},
                                {"name": "Urgent", "color": "red"}
                            ]
                        }
                    },
                    "Category": {
                        "rich_text": {}
                    },
                    "Date": {
                        "date": {}
                    },
                    "Due Date": {
                        "date": {}
                    },
                    "Notes": {
                        "rich_text": {}
                    },
                    "Employee": {
                        "rich_text": {}
                    },
                    "Is Recurring": {
                        "checkbox": {}
                    },
                    "Reminder Sent": {
                        "checkbox": {}
                    }
                }
            )
            
            database_id = database["id"]
            logger.info(f"Created task database for user {user.email}: {database_id}")
            
            return database_id
            
        except Exception as e:
            logger.error(f"Failed to create task database for user {user.email}: {str(e)}")
            raise Exception(f"Failed to create task database: {str(e)}")
    
    def get_user_task_database_id(self, user: User) -> Optional[str]:
        """
        Get the task database ID for a user.
        
        Args:
            user: The user object.
            
        Returns:
            Optional[str]: The task database ID if it exists, None otherwise.
        """
        return user.task_database_id
    
    def set_user_task_database_id(self, user: User, database_id: str) -> None:
        """
        Set the task database ID for a user.
        
        Args:
            user: The user object.
            database_id: The task database ID.
        """
        user.task_database_id = database_id
    
    def create_task_in_user_database(self, user: User, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a task in the user's personal task database.
        
        Args:
            user: The user object.
            task_data: The task data to create.
            
        Returns:
            Dict[str, Any]: The created task data.
        """
        if not user.task_database_id:
            raise ValueError("User does not have a task database assigned")
        
        try:
            # Format task properties for Notion
            properties = {
                "Task": {
                    "title": [
                        {
                            "text": {
                                "content": task_data.get("task", "")
                            }
                        }
                    ]
                },
                "Status": {
                    "select": {
                        "name": task_data.get("status", "Not Started")
                    }
                },
                "Priority": {
                    "select": {
                        "name": task_data.get("priority", "Medium")
                    }
                },
                "Category": {
                    "rich_text": [
                        {
                            "text": {
                                "content": task_data.get("category", "")
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": task_data.get("date")
                    } if task_data.get("date") else None
                },
                "Due Date": {
                    "date": {
                        "start": task_data.get("due_date")
                    } if task_data.get("due_date") else None
                },
                "Notes": {
                    "rich_text": [
                        {
                            "text": {
                                "content": task_data.get("notes", "")
                            }
                        }
                    ]
                },
                "Employee": {
                    "rich_text": [
                        {
                            "text": {
                                "content": task_data.get("employee", user.full_name)
                            }
                        }
                    ]
                },
                "Is Recurring": {
                    "checkbox": task_data.get("is_recurring", False)
                },
                "Reminder Sent": {
                    "checkbox": task_data.get("reminder_sent", False)
                }
            }
            
            # Remove None values
            properties = {k: v for k, v in properties.items() if v is not None}
            
            response = self.notion_client.pages.create(
                parent={"database_id": user.task_database_id},
                properties=properties
            )
            
            # Return the created task data
            created_task = {
                "id": response["id"],
                "task": task_data.get("task", ""),
                "status": task_data.get("status", "Not Started"),
                "priority": task_data.get("priority", "Medium"),
                "category": task_data.get("category", ""),
                "due_date": task_data.get("due_date"),
                "notes": task_data.get("notes", ""),
                "assigned_to": task_data.get("employee", user.full_name),
                "created_time": response.get("created_time"),
                "last_edited_time": response.get("last_edited_time")
            }
            
            logger.info(f"Created task in user database for {user.email}: {created_task['task']}")
            return created_task
            
        except Exception as e:
            logger.error(f"Failed to create task in user database for {user.email}: {str(e)}")
            raise Exception(f"Failed to create task: {str(e)}")
    
    def get_user_tasks(self, user: User, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get tasks from the user's personal task database.
        
        Args:
            user: The user object.
            days_back: Number of days back to fetch tasks for.
            
        Returns:
            List[Dict[str, Any]]: List of user's tasks.
        """
        if not user.task_database_id:
            return []
        
        try:
            response = self.notion_client.databases.query(
                database_id=user.task_database_id
            )
            
            tasks = []
            for page in response.get("results", []):
                task = self._process_task_page(page)
                if task:
                    tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} tasks for user {user.email}")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get tasks for user {user.email}: {str(e)}")
            return []
    
    def update_user_task(self, user: User, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a task in the user's personal task database.
        
        Args:
            user: The user object.
            task_id: The task ID to update.
            updates: The updates to apply.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not user.task_database_id:
            return False
        
        try:
            # Format updates for Notion
            properties = {}
            
            if "task" in updates:
                properties["Task"] = {
                    "title": [
                        {
                            "text": {
                                "content": updates["task"]
                            }
                        }
                    ]
                }
            
            if "status" in updates:
                properties["Status"] = {
                    "select": {
                        "name": updates["status"]
                    }
                }
            
            if "priority" in updates:
                properties["Priority"] = {
                    "select": {
                        "name": updates["priority"]
                    }
                }
            
            if "category" in updates:
                properties["Category"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": updates["category"]
                            }
                        }
                    ]
                }
            
            if "due_date" in updates:
                properties["Due Date"] = {
                    "date": {
                        "start": updates["due_date"]
                    } if updates["due_date"] else None
                }
            
            if "date" in updates:
                properties["Date"] = {
                    "date": {
                        "start": updates["date"]
                    } if updates["date"] else None
                }
            
            if "notes" in updates:
                properties["Notes"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": updates["notes"]
                            }
                        }
                    ]
                }
            
            if "employee" in updates:
                properties["Employee"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": updates["employee"]
                            }
                        }
                    ]
                }
            
            if "is_recurring" in updates:
                properties["Is Recurring"] = {
                    "checkbox": updates["is_recurring"]
                }
            
            if "reminder_sent" in updates:
                properties["Reminder Sent"] = {
                    "checkbox": updates["reminder_sent"]
                }
            
            # Remove None values
            properties = {k: v for k, v in properties.items() if v is not None}
            
            if properties:
                self.notion_client.pages.update(
                    page_id=task_id,
                    properties=properties
                )
                
                logger.info(f"Updated task {task_id} for user {user.email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id} for user {user.email}: {str(e)}")
            return False
    
    def delete_user_task(self, user: User, task_id: str) -> bool:
        """
        Delete a task from the user's personal task database.
        
        Args:
            user: The user object.
            task_id: The task ID to delete.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not user.task_database_id:
            return False
        
        try:
            self.notion_client.pages.update(
                page_id=task_id,
                archived=True
            )
            
            logger.info(f"Deleted task {task_id} for user {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete task {task_id} for user {user.email}: {str(e)}")
            return False
    
    def _process_task_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a Notion page into a task dictionary.
        
        Args:
            page: Notion page data.
            
        Returns:
            Optional[Dict[str, Any]]: Processed task data.
        """
        try:
            properties = page.get("properties", {})
            
            task = {
                "id": page["id"],
                "task": self._extract_title(properties.get("Task", {})),
                "status": self._extract_select(properties.get("Status", {}), "Not Started"),
                "priority": self._extract_select(properties.get("Priority", {}), "Medium"),
                "category": self._extract_rich_text(properties.get("Category", {})),
                "date": self._extract_date(properties.get("Date", {})),
                "due_date": self._extract_date(properties.get("Due Date", {})),
                "notes": self._extract_rich_text(properties.get("Notes", {})),
                "employee": self._extract_rich_text(properties.get("Employee", {})),
                "is_recurring": properties.get("Is Recurring", {}).get("checkbox", False),
                "reminder_sent": properties.get("Reminder Sent", {}).get("checkbox", False),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time")
            }
            
            return task
            
        except Exception as e:
            logger.error(f"Error processing task page {page.get('id')}: {str(e)}")
            return None
    
    def _extract_title(self, property_data: Dict[str, Any]) -> str:
        """Extract title from Notion property."""
        return property_data.get("title", [{}])[0].get("text", {}).get("content", "")
    
    def _extract_rich_text(self, property_data: Dict[str, Any]) -> str:
        """Extract rich text from Notion property."""
        return property_data.get("rich_text", [{}])[0].get("text", {}).get("content", "")
    
    def _extract_select(self, property_data: Dict[str, Any], default: str = None) -> str:
        """Extract select value from Notion property."""
        return property_data.get("select", {}).get("name", default)
    
    def _extract_date(self, property_data: Dict[str, Any]) -> Optional[str]:
        """Extract date from Notion property."""
        return property_data.get("date", {}).get("start") 
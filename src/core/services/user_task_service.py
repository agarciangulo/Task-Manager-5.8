"""
Service for managing user-specific task databases in Notion.
"""
import uuid
from typing import Optional, Dict, Any, List
from notion_client import Client
from datetime import datetime

from src.core.models.user import User
from src.core.logging_config import get_logger
from src.plugins.plugin_manager_instance import plugin_manager

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
        
        # Get the project protection plugin
        self.protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')
    
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
                    "Title": {
                        "title": {}
                    },
                    "Task": {
                        "rich_text": {}
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
            
            # Reorder properties to ensure Title comes first, then Task
            self._reorder_database_properties(database_id)
            
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
            # Apply protection to task data before sending to Notion
            protected_task_data = task_data
            if self.protection_plugin and self.protection_plugin.enabled:
                protected_task_data = self.protection_plugin.protect_task(task_data)
            
            # Format task properties for Notion
            properties = {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": protected_task_data.get("title", "")
                            }
                        }
                    ]
                },
                "Task": {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_task_data.get("task", "")
                            }
                        }
                    ]
                },
                "Status": {
                    "select": {
                        "name": protected_task_data.get("status", "Not Started")
                    }
                },
                "Priority": {
                    "select": {
                        "name": protected_task_data.get("priority", "Medium")
                    }
                },
                "Category": {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_task_data.get("category", "")
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": protected_task_data.get("date")
                    } if protected_task_data.get("date") else None
                },
                "Due Date": {
                    "date": {
                        "start": protected_task_data.get("due_date")
                    } if protected_task_data.get("due_date") else None
                },
                "Notes": {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_task_data.get("notes", "")
                            }
                        }
                    ]
                },
                "Employee": {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_task_data.get("employee", user.full_name)
                            }
                        }
                    ]
                },
                "Is Recurring": {
                    "checkbox": protected_task_data.get("is_recurring", False)
                },
                "Reminder Sent": {
                    "checkbox": protected_task_data.get("reminder_sent", False)
                }
            }
            
            # Remove None values
            properties = {k: v for k, v in properties.items() if v is not None}
            
            response = self.notion_client.pages.create(
                parent={"database_id": user.task_database_id},
                properties=properties
            )
            
            # Return the created task data (with original names, not tokens)
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
            # Apply protection to updates before sending to Notion
            protected_updates = updates
            if self.protection_plugin and self.protection_plugin.enabled:
                protected_updates = self.protection_plugin.protect_task(updates)
            
            # Format updates for Notion
            properties = {}
            
            if "title" in protected_updates:
                properties["Title"] = {
                    "title": [
                        {
                            "text": {
                                "content": protected_updates["title"]
                            }
                        }
                    ]
                }
            
            if "task" in protected_updates:
                properties["Task"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_updates["task"]
                            }
                        }
                    ]
                }
            
            if "status" in protected_updates:
                properties["Status"] = {
                    "select": {
                        "name": protected_updates["status"]
                    }
                }
            
            if "priority" in protected_updates:
                properties["Priority"] = {
                    "select": {
                        "name": protected_updates["priority"]
                    }
                }
            
            if "category" in protected_updates:
                properties["Category"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_updates["category"]
                            }
                        }
                    ]
                }
            
            if "due_date" in protected_updates:
                properties["Due Date"] = {
                    "date": {
                        "start": protected_updates["due_date"]
                    } if protected_updates["due_date"] else None
                }
            
            if "date" in protected_updates:
                properties["Date"] = {
                    "date": {
                        "start": protected_updates["date"]
                    } if protected_updates["date"] else None
                }
            
            if "notes" in protected_updates:
                properties["Notes"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_updates["notes"]
                            }
                        }
                    ]
                }
            
            if "employee" in protected_updates:
                properties["Employee"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": protected_updates["employee"]
                            }
                        }
                    ]
                }
            
            if "is_recurring" in protected_updates:
                properties["Is Recurring"] = {
                    "checkbox": protected_updates["is_recurring"]
                }
            
            if "reminder_sent" in protected_updates:
                properties["Reminder Sent"] = {
                    "checkbox": protected_updates["reminder_sent"]
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
                "title": self._extract_title(properties.get("Title", {})),
                "task": self._extract_rich_text(properties.get("Task", {})),
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
            
            # Restore original project names from tokens
            if self.protection_plugin and self.protection_plugin.enabled:
                task = self.protection_plugin.unprotect_task(task)
            
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

    def _reorder_database_properties(self, database_id: str) -> None:
        """
        Reorder properties of the database to ensure Title comes first, then Task.
        
        Args:
            database_id: The database ID to reorder properties for.
        """
        try:
            # Define the desired property order
            desired_order = [
                "Title",
                "Task", 
                "Status",
                "Priority",
                "Category",
                "Date",
                "Due Date",
                "Notes",
                "Employee",
                "Is Recurring",
                "Reminder Sent"
            ]
            
            # Get current database to see existing properties
            database = self.notion_client.databases.retrieve(database_id=database_id)
            current_properties = database.get("properties", {})
            
            # Create new properties dict in desired order
            reordered_properties = {}
            for prop_name in desired_order:
                if prop_name in current_properties:
                    reordered_properties[prop_name] = current_properties[prop_name]
            
            # Add any remaining properties that weren't in our desired order
            for prop_name, prop_data in current_properties.items():
                if prop_name not in reordered_properties:
                    reordered_properties[prop_name] = prop_data
            
            # Update the database with reordered properties
            self.notion_client.databases.update(
                database_id=database_id,
                properties=reordered_properties
            )
            
            logger.info(f"Successfully reordered properties for database {database_id}")
            
        except Exception as e:
            logger.warning(f"Failed to reorder properties for database {database_id}: {str(e)}")
            # Don't fail the entire operation if reordering fails 
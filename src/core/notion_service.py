import os
from notion_client import Client
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd
from typing import List, Dict, Optional, Any
from src.config.settings import (
    NOTION_TOKEN,
    NOTION_DATABASE_ID,
    NOTION_FEEDBACK_DB_ID,
    NOTION_USERS_DB_ID,
    NOTION_PARENT_PAGE_ID,
    DEBUG_MODE,
    DAYS_THRESHOLD
)
from src.core.logging_config import get_logger
from src.plugins.plugin_manager_instance import plugin_manager

logger = get_logger(__name__)

class NotionService:
    def __init__(self, token=None, feedback_db_id=None):
        self.token = token or NOTION_TOKEN
        self.feedback_db_id = feedback_db_id or NOTION_FEEDBACK_DB_ID
        self.client = Client(auth=self.token)
        self._cache = {}
        self._cache_timestamp = None
        self._cache_valid_duration = timedelta(minutes=5)
        
        # Get the project protection plugin
        self.protection_plugin = plugin_manager.get_plugin('ProjectProtectionPlugin')

    def debug_print(self, message):
        if DEBUG_MODE:
            print(message)

    def validate_connection(self) -> bool:
        """
        Validate the connection to Notion.
        
        Returns:
            bool: True if connection is valid, False otherwise.
        """
        try:
            # Try to fetch a known database to validate connection
            # Note: This now uses the feedback DB or a provided one, as task_db_id is no longer global
            self.client.databases.retrieve(database_id=self.feedback_db_id)
            logger.info("Notion connection successful")
            return True
        except Exception as e:
            logger.error("Notion connection failed", extra={"error": str(e)})
            return False

    def fetch_tasks(self, database_id: str, days_back: int = 30) -> pd.DataFrame:
        """
        Fetch tasks from a specific Notion database and return as a pandas DataFrame.
        Args:
            database_id: The ID of the Notion database to fetch tasks from.
            days_back: Number of days back to fetch tasks for.
        Returns:
            pd.DataFrame: DataFrame of tasks.
        """
        try:
            # Caching is now per-database
            cache_key = f"tasks_{database_id}"
            if self._is_cache_valid(cache_key):
                logger.debug(f"Returning cached tasks for database {database_id}")
                return pd.DataFrame(list(self._cache[cache_key].values()))

            # Calculate date filter (leave blank to fetch all, but keep infrastructure)
            filter_params = {}
            # Fetch from Notion
            logger.info(f"Fetching tasks from Notion database: {database_id}", extra={"days_back": days_back})
            response = self.client.databases.query(
                database_id=database_id,
                **filter_params
            )
            # Process results
            tasks = []
            for page in response.get("results", []):
                try:
                    task = self._process_notion_page(page)
                    if task:
                        tasks.append(task)
                        # Initialize per-db cache if not present
                        if cache_key not in self._cache:
                            self._cache[cache_key] = {}
                        self._cache[cache_key][task["id"]] = task
                except Exception as e:
                    logger.error("Error processing Notion page", 
                               extra={
                                   "page_id": page["id"],
                                   "error": str(e)
                               })
            # Update cache timestamp
            self._cache_timestamp = datetime.now() # This timestamp is now for the whole cache object
            logger.info(f"Successfully fetched tasks from {database_id}", extra={"count": len(tasks)})
            return pd.DataFrame(tasks)
        except Exception as e:
            import traceback
            logger.error(f"Error fetching tasks from {database_id}: {e}\n{traceback.format_exc()}")
            print(f"Error fetching tasks: {e}")
            print(traceback.format_exc())
            return pd.DataFrame([])

    def insert_task(self, database_id: str, task_data: Dict[str, Any]) -> tuple:
        """
        Insert a new task into a specific Notion database.
        Returns:
            tuple: (True, message) if successful, (False, error message) otherwise.
        """
        try:
            response = self.client.pages.create(
                parent={"database_id": database_id},
                properties=self._format_task_properties(task_data)
            )
            task = self._process_notion_page(response)
            # Update per-db cache
            cache_key = f"tasks_{database_id}"
            if task:
                if cache_key not in self._cache:
                    self._cache[cache_key] = {}
                self._cache[cache_key][task["id"]] = task
            logger.info(f"Successfully inserted task into {database_id}", extra={"task_id": task["id"]})
            return True, "Task inserted successfully"
        except Exception as e:
            import traceback
            error_details = f"Error inserting task into {database_id}: {str(e)}\nTask data: {task_data}\nTraceback: {traceback.format_exc()}"
            logger.error(error_details)
            print(f"❌ {error_details}")  # Also print to console for debugging
            return False, str(e)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> tuple:
        """
        Update a task in Notion. The database is inferred from the task_id.
        Returns:
            tuple: (True, message) if successful, (False, error message) otherwise.
        """
        try:
            response = self.client.pages.update(
                page_id=task_id,
                properties=self._format_task_properties(updates)
            )
            task = self._process_notion_page(response)
            
            # This is tricky because we don't know the DB ID from the task ID alone.
            # We would need to search all cached DBs or skip caching on update.
            # For simplicity, we'll skip cache update here. A better solution might involve
            # passing the DB ID to update_task as well.
            
            logger.info("Successfully updated task", extra={"task_id": task_id})
            return True, "Task updated successfully"
        except Exception as e:
            logger.error("Error updating task", 
                        extra={
                            "task_id": task_id,
                            "error": str(e)
                        })
            return False, str(e)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID from Notion.
        
        Args:
            task_id: The Notion page ID of the task.
            
        Returns:
            Optional[Dict[str, Any]]: Task data if found, None otherwise.
        """
        try:
            response = self.client.pages.retrieve(page_id=task_id)
            task = self._process_notion_page(response)
            
            if task:
                logger.info("Successfully retrieved task", extra={"task_id": task_id})
                return task
            else:
                logger.warning("Task not found or could not be processed", extra={"task_id": task_id})
                return None
                
        except Exception as e:
            logger.error("Error retrieving task", 
                        extra={
                            "task_id": task_id,
                            "error": str(e)
                        })
            return None

    def delete_task(self, task_id: str) -> tuple:
        """
        Delete (archive) a task in Notion.
        
        Args:
            task_id: The Notion page ID of the task to delete.
            
        Returns:
            tuple: (True, message) if successful, (False, error message) otherwise.
        """
        try:
            # In Notion, "deleting" is actually archiving the page
            response = self.client.pages.update(
                page_id=task_id,
                archived=True
            )
            
            logger.info("Successfully archived task", extra={"task_id": task_id})
            return True, "Task archived successfully"
            
        except Exception as e:
            logger.error("Error archiving task", 
                        extra={
                            "task_id": task_id,
                            "error": str(e)
                        })
            return False, str(e)

    def fetch_peer_feedback(self, person_name: str, days_back: int = 14) -> List[Dict[str, Any]]:
        # Example: fetch feedback for a person in the last N days
        # (Implement as needed for your schema)
        return []

    # --- Helper methods for Notion property extraction ---
    def get_title_content(self, props, key):
        try:
            return props[key]["title"][0]["plain_text"] if props[key]["title"] else ""
        except Exception:
            return ""
    def get_select_value(self, props, key, default=None):
        try:
            return props[key]["select"]["name"] if props[key]["select"] else default
        except Exception:
            return default
    def get_rich_text_content(self, props, key):
        try:
            return props[key]["rich_text"][0]["plain_text"] if props[key]["rich_text"] else ""
        except Exception:
            return ""
    def get_date_value(self, props, key):
        try:
            return props[key]["date"]["start"] if props[key]["date"] else None
        except Exception:
            return None
    def get_checkbox_value(self, props, key, default=False):
        try:
            return props[key]["checkbox"] if "checkbox" in props[key] else default
        except Exception:
            return default
    def build_notion_properties(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Build Notion properties dict from task fields (implement as needed)
        # This is a placeholder; adapt to your schema
        return {
            "Title": {"title": [{"text": {"content": task.get("title", "")}}]},
            "Task": {"rich_text": [{"text": {"content": task.get("task", "")}}]},
            "Status": {"select": {"name": task.get("status", "No Status")}},
            "Employee": {"rich_text": [{"text": {"content": task.get("employee", "")}}]},
            "Date": {"date": {"start": task.get("date")}},
            "Reminder Sent": {"checkbox": task.get("reminder_sent", False)},
            "Category": {"rich_text": [{"text": {"content": task.get("category", "")}}]},
            "Notes": {"rich_text": [{"text": {"content": task.get("notes", "")}}]},
            "Is Recurring": {"checkbox": task.get("is_recurring", False)}
        }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if the cache for a specific key is still valid.
        
        Returns:
            bool: True if cache is valid, False otherwise.
        """
        if not self._cache_timestamp or cache_key not in self._cache:
            return False
        
        age = datetime.now() - self._cache_timestamp
        return age < self._cache_valid_duration
    
    def _process_notion_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a Notion page into a task dictionary.
        
        Args:
            page: Notion page data.
            
        Returns:
            Optional[Dict[str, Any]]: Processed task data.
        """
        try:
            properties = page.get("properties", {})
            
            # Extract task data
            task = {
                "id": page["id"],
                "title": self.get_title_content(properties, "Title"),
                "task": self.get_title_content(properties, "Task"),
                "status": self.get_select_value(properties, "Status", "Not Started"),
                "employee": self.get_rich_text_content(properties, "Employee"),
                "date": self.get_date_value(properties, "Date"),
                "category": self.get_rich_text_content(properties, "Category"),
                "priority": self.get_select_value(properties, "Priority", "Medium"),
                "due_date": self.get_date_value(properties, "Due Date"),
                "notes": self.get_rich_text_content(properties, "Notes"),
                "is_recurring": self.get_checkbox_value(properties, "Is Recurring", False),
                "reminder_sent": self.get_checkbox_value(properties, "Reminder Sent", False),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time")
            }
            
            # Restore original project names from tokens
            if self.protection_plugin and self.protection_plugin.enabled:
                task = self.protection_plugin.unprotect_task(task)
            
            return task
            
        except Exception as e:
            logger.error("Error processing Notion page", 
                        extra={
                            "page_id": page.get("id"),
                            "error": str(e)
                        })
            return None
    
    def _format_task_properties(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format task data for Notion API.
        Args:
            task_data: Task data to format.
        Returns:
            Dict[str, Any]: Formatted properties.
        """
        # Apply protection to task data before sending to Notion
        protected_task_data = task_data
        if self.protection_plugin and self.protection_plugin.enabled:
            protected_task_data = self.protection_plugin.protect_task(task_data)
        
        properties = {}
        # Title
        if "title" in protected_task_data and protected_task_data["title"]:
            properties["Title"] = {
                "title": [
                    {
                        "text": {
                            "content": protected_task_data["title"]
                        }
                    }
                ]
            }
        # Task description (rich_text)
        if "task" in protected_task_data and protected_task_data["task"]:
            properties["Task"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": protected_task_data["task"]
                        }
                    }
                ]
            }
        # Status
        if "status" in protected_task_data:
            properties["Status"] = {
                "select": {
                    "name": protected_task_data["status"]
                }
            }
        # Employee
        if "employee" in protected_task_data and protected_task_data["employee"]:
            properties["Employee"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": protected_task_data["employee"]
                        }
                    }
                ]
            }
        # Date
        if "date" in protected_task_data and protected_task_data["date"]:
            properties["Date"] = {
                "date": {
                    "start": protected_task_data["date"]
                }
            }
        # Category
        if "category" in protected_task_data and protected_task_data["category"]:
            properties["Category"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": protected_task_data["category"]
                        }
                    }
                ]
            }
        # Priority
        if "priority" in protected_task_data:
            properties["Priority"] = {
                "select": {
                    "name": protected_task_data["priority"]
                }
            }
        # Due Date
        if "due_date" in protected_task_data and protected_task_data["due_date"]:
            properties["Due Date"] = {
                "date": {
                    "start": protected_task_data["due_date"]
                }
            }
        # Notes
        if "notes" in protected_task_data and protected_task_data["notes"]:
            properties["Notes"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": protected_task_data["notes"]
                        }
                    }
                ]
            }
        # Is Recurring
        if "is_recurring" in protected_task_data:
            properties["Is Recurring"] = {
                "checkbox": protected_task_data["is_recurring"]
            }
        # Reminder Sent
        if "reminder_sent" in protected_task_data:
            properties["Reminder Sent"] = {
                "checkbox": protected_task_data["reminder_sent"]
            }
        
        logger.debug(f"Formatting task properties. Input: {task_data}, Protected: {protected_task_data}, Output: {properties}")
        return properties

    def identify_stale_tasks(self, database_id: str, days: int = 7) -> list:
        """
        Identify tasks not updated in the last `days` days from a specific database.
        """
        try:
            tasks_df = self.fetch_tasks(database_id=database_id, days_back=30)
            if tasks_df.empty:
                return []
                
            cutoff = datetime.now() - timedelta(days=days)
            stale = []
            
            for _, task in tasks_df.iterrows():
                if task.get('last_edited_time'):
                    try:
                        last_edited = parser.parse(task['last_edited_time'])
                        if last_edited < cutoff:
                            stale.append(task.to_dict())
                    except:
                        pass  # Skip tasks with invalid dates
                        
            logger.info("Identified stale tasks", extra={"count": len(stale), "days": days, "database_id": database_id})
            return stale
        except Exception as e:
            logger.error("Error identifying stale tasks", extra={"error": str(e), "database_id": database_id})
            return [] 

    def mark_task_as_reminded(self, task_id: str) -> bool:
        """
        Placeholder for marking a task as reminded. To be implemented.
        """
        logger.info("Called mark_task_as_reminded (placeholder)", extra={"task_id": task_id})
        return True

    def list_all_categories(self, database_id: str) -> list:
        """
        Return a list of all unique categories from a specific Notion database.
        """
        try:
            tasks_df = self.fetch_tasks(database_id=database_id)
            if tasks_df.empty:
                return []
                
            if "category" in tasks_df.columns:
                categories = tasks_df["category"].dropna().unique().tolist()
                return sorted([c for c in categories if c])
            else:
                return []
        except Exception as e:
            logger.error("Error listing categories", extra={"error": str(e), "database_id": database_id})
            return [] 
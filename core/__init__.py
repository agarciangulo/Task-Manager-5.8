"""
Core package for Task Manager.
This module provides compatibility with the new structure.
"""
# Import from new locations
# from core.notion_service import NotionService  # Commented out to avoid circular import

# Functions from notion_service.py - updated to accept database_id
def fetch_notion_tasks(database_id: str, days_back: int = 30):
    """Fetch tasks from a specific database."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.fetch_tasks(database_id=database_id, days_back=days_back)

def identify_stale_tasks(database_id: str, days: int = 7):
    """Identify stale tasks in a specific database."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.identify_stale_tasks(database_id=database_id, days=days)

def mark_task_as_reminded(task_id: str):
    """Mark a task as reminded."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.mark_task_as_reminded(task_id)

def insert_task_to_notion(database_id: str, task_data: dict):
    """Insert a task into a specific database."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.insert_task(database_id=database_id, task_data=task_data)

def update_task_in_notion(task_id: str, updates: dict):
    """Update a task in Notion."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.update_task(task_id=task_id, updates=updates)

def fetch_peer_feedback(person_name: str, days_back: int = 14):
    """Fetch peer feedback."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.fetch_peer_feedback(person_name, days_back)

def list_all_categories(database_id: str):
    """List all categories from a specific database."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.list_all_categories(database_id=database_id)

def validate_notion_connection():
    """Validate Notion connection."""
    from core.notion_service import NotionService
    service = NotionService()
    return service.validate_connection()

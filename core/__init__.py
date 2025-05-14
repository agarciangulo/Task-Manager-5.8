"""
Core package for Task Manager.
This module provides compatibility with the new structure.
"""
# Import from new locations
from core.notion_service import NotionService

# Create instance with default config
notion_service = NotionService()

# Functions from notion_service.py
fetch_notion_tasks = notion_service.fetch_tasks
identify_stale_tasks = notion_service.identify_stale_tasks
mark_task_as_reminded = notion_service.mark_task_as_reminded
insert_task_to_notion = notion_service.insert_task
update_task_in_notion = notion_service.update_task
fetch_peer_feedback = notion_service.fetch_peer_feedback
list_all_categories = notion_service.list_all_categories
validate_notion_connection = notion_service.validate_connection

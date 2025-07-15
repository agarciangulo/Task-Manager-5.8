from src.core.notion_service import NotionService
from src.core.exceptions import handle_agent_errors, NotionAgentError

class NotionAgent:
    """Agent for all Notion API operations."""
    def __init__(self):
        self.service = NotionService()

    @handle_agent_errors("NotionAgent")
    def fetch_tasks(self, database_id: str):
        try:
            return self.service.fetch_tasks(database_id=database_id)
        except Exception as e:
            import traceback
            print(f"Error fetching tasks: {e}")
            print(traceback.format_exc())
            raise ValueError(f"Failed to fetch tasks: {str(e)}\n{traceback.format_exc()}")

    @handle_agent_errors("NotionAgent")
    def insert_task(self, database_id: str, task: dict):
        try:
            return self.service.insert_task(database_id=database_id, task_data=task)
        except Exception as e:
            raise NotionAgentError(f"Failed to insert task: {e}")

    @handle_agent_errors("NotionAgent")
    def update_task(self, task_id: str, task: dict):
        try:
            return self.service.update_task(task_id=task_id, updates=task)
        except Exception as e:
            raise NotionAgentError(f"Failed to update task: {e}")

    @handle_agent_errors("NotionAgent")
    def fetch_peer_feedback(self, person_name, days_back=14):
        try:
            return self.service.fetch_peer_feedback(person_name, days_back)
        except Exception as e:
            import traceback
            print(f"Error fetching peer feedback: {e}")
            print(traceback.format_exc())
            raise ValueError(f"Failed to fetch peer feedback: {str(e)}\n{traceback.format_exc()}")

    @handle_agent_errors("NotionAgent")
    def validate_connection(self):
        try:
            return self.service.validate_connection()
        except Exception as e:
            raise NotionAgentError(f"Failed to validate Notion connection: {e}")

 
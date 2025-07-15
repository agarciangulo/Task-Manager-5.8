from src.core.task_extractor import extract_tasks_from_update
from src.core.exceptions import handle_agent_errors, TaskExtractionAgentError

class TaskExtractionAgent:
    """Agent for extracting structured tasks from freeform text."""
    @handle_agent_errors("TaskExtractionAgent")
    def extract_tasks(self, text: str):
        try:
            return extract_tasks_from_update(text)
        except Exception as e:
            import traceback
            print(f"Error extracting tasks: {e}")
            print(traceback.format_exc())
            raise ValueError(f"Task extraction failed: {str(e)}\n{traceback.format_exc()}") 
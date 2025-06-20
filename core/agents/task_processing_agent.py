from core.task_processor import insert_or_update_task, batch_insert_tasks
from core.exceptions import handle_agent_errors, TaskProcessingError

class TaskProcessingAgent:
    """Agent for processing tasks: similarity checking, insertion, updating."""
    @handle_agent_errors("TaskProcessingAgent")
    def process_task(self, database_id: str, task, existing_tasks, log_output=None, batch_mode=False):
        try:
            return insert_or_update_task(database_id, task, existing_tasks, log_output, batch_mode)
        except Exception as e:
            import traceback
            print(f"Error processing task: {e}")
            print(traceback.format_exc())
            raise ValueError(f"Task processing failed: {str(e)}\n{traceback.format_exc()}")

    @handle_agent_errors("TaskProcessingAgent")
    def batch_process_tasks(self, database_id: str, tasks, existing_tasks):
        try:
            return batch_insert_tasks(database_id, tasks, existing_tasks)
        except Exception as e:
            raise TaskProcessingError(f"Failed to batch process tasks: {e}") 
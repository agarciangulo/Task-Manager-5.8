"""
Asynchronous Notion tasks for Task Manager.
Handles database operations without blocking the main application.
"""
import traceback
from typing import Dict, List, Any, Optional
from celery import current_task
from celery_config import celery_app
from core.notion_service import NotionService
from core.logging_config import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, name='core.tasks.notion_tasks.fetch_tasks_async')
def fetch_tasks_async(self, database_id: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Asynchronously fetch tasks from Notion database.
    
    Args:
        database_id: The Notion database ID
        days_back: Number of days back to fetch
        
    Returns:
        Dict with success status and data/error
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Connecting to Notion...'}
        )
        
        notion_service = NotionService()
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Fetching tasks...'}
        )
        
        # Fetch tasks
        df = notion_service.fetch_tasks(database_id, days_back)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Processing results...'}
        )
        
        # Convert DataFrame to dict for JSON serialization
        tasks_data = df.to_dict('records') if not df.empty else []
        
        logger.info(f"Successfully fetched {len(tasks_data)} tasks from database {database_id}")
        
        return {
            'success': True,
            'data': tasks_data,
            'count': len(tasks_data),
            'database_id': database_id
        }
        
    except Exception as e:
        logger.error(f"Error fetching tasks from {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id
        }

@celery_app.task(bind=True, name='core.tasks.notion_tasks.insert_task_async')
def insert_task_async(self, database_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronously insert a task into Notion database.
    
    Args:
        database_id: The Notion database ID
        task_data: Task data to insert
        
    Returns:
        Dict with success status and result/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Preparing task...'}
        )
        
        notion_service = NotionService()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Inserting task...'}
        )
        
        success, message = notion_service.insert_task(database_id, task_data)
        
        if success:
            logger.info(f"Successfully inserted task into database {database_id}")
            return {
                'success': True,
                'message': message,
                'database_id': database_id,
                'task_data': task_data
            }
        else:
            logger.error(f"Failed to insert task into {database_id}: {message}")
            return {
                'success': False,
                'error': message,
                'database_id': database_id,
                'task_data': task_data
            }
            
    except Exception as e:
        logger.error(f"Error inserting task into {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id,
            'task_data': task_data
        }

@celery_app.task(bind=True, name='core.tasks.notion_tasks.update_task_async')
def update_task_async(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronously update a task in Notion.
    
    Args:
        task_id: The Notion task ID
        updates: Updates to apply
        
    Returns:
        Dict with success status and result/error
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Preparing update...'}
        )
        
        notion_service = NotionService()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Updating task...'}
        )
        
        success, message = notion_service.update_task(task_id, updates)
        
        if success:
            logger.info(f"Successfully updated task {task_id}")
            return {
                'success': True,
                'message': message,
                'task_id': task_id,
                'updates': updates
            }
        else:
            logger.error(f"Failed to update task {task_id}: {message}")
            return {
                'success': False,
                'error': message,
                'task_id': task_id,
                'updates': updates
            }
            
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'task_id': task_id,
            'updates': updates
        }

@celery_app.task(bind=True, name='core.tasks.notion_tasks.batch_insert_tasks_async')
def batch_insert_tasks_async(self, database_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Asynchronously insert multiple tasks into Notion database.
    
    Args:
        database_id: The Notion database ID
        tasks: List of task data to insert
        
    Returns:
        Dict with success status and results
    """
    try:
        notion_service = NotionService()
        results = []
        successful = 0
        failed = 0
        
        for i, task_data in enumerate(tasks):
            # Update progress
            progress = int((i / len(tasks)) * 100)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': f'Inserting task {i+1}/{len(tasks)}...'
                }
            )
            
            try:
                success, message = notion_service.insert_task(database_id, task_data)
                results.append({
                    'task': task_data.get('task', 'Unknown'),
                    'success': success,
                    'message': message
                })
                
                if success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                results.append({
                    'task': task_data.get('task', 'Unknown'),
                    'success': False,
                    'message': str(e)
                })
                failed += 1
        
        logger.info(f"Batch insert completed: {successful} successful, {failed} failed")
        
        return {
            'success': True,
            'results': results,
            'summary': {
                'total': len(tasks),
                'successful': successful,
                'failed': failed
            },
            'database_id': database_id
        }
        
    except Exception as e:
        logger.error(f"Error in batch insert for {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id,
            'tasks': tasks
        }

@celery_app.task(bind=True, name='core.tasks.notion_tasks.identify_stale_tasks_async')
def identify_stale_tasks_async(self, database_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Asynchronously identify stale tasks in Notion database.
    
    Args:
        database_id: The Notion database ID
        days: Number of days to consider for stale tasks
        
    Returns:
        Dict with stale tasks data
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Analyzing tasks...'}
        )
        
        notion_service = NotionService()
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Identifying stale tasks...'}
        )
        
        stale_tasks = notion_service.identify_stale_tasks(database_id, days)
        
        logger.info(f"Identified {len(stale_tasks)} stale tasks in database {database_id}")
        
        return {
            'success': True,
            'stale_tasks': stale_tasks,
            'count': len(stale_tasks),
            'database_id': database_id,
            'days_threshold': days
        }
        
    except Exception as e:
        logger.error(f"Error identifying stale tasks in {database_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'database_id': database_id,
            'days_threshold': days
        } 
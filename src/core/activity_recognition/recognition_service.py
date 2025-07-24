"""
AI-powered activity recognition service for identifying recurring activities.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.core.services.activity_service import ActivityDataService
from src.core.chroma_embedding_manager_simple import SimpleChromaEmbeddingManager
from src.core.ai.analyzers import get_ai_response
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ActivityRecognitionService:
    """
    AI-powered service for recognizing and tracking recurring activities.
    """
    
    def __init__(self, user_id: str, db_session: Session):
        """
        Initialize the activity recognition service.
        
        Args:
            user_id: User identifier
            db_session: Database session
        """
        self.user_id = user_id
        self.db_session = db_session
        self.chroma_manager = SimpleChromaEmbeddingManager()
        self.activity_service = ActivityDataService(db_session)
        
        logger.info(f"Initialized ActivityRecognitionService for user {user_id}")
    
    def process_new_task(self, task_id: str, task_title: str) -> Dict[str, Any]:
        """
        Process a new task to identify if it belongs to an existing activity.
        
        Args:
            task_id: Task identifier
            task_title: Task title/description
            
        Returns:
            Dict[str, Any]: Processing results
        """
        try:
            logger.info(f"Processing new task for user {self.user_id}: {task_title[:50]}...")
            
            # Step 1: Get vector embedding for the task title
            task_embedding = self.chroma_manager.get_embedding(task_title)
            if task_embedding is None:
                logger.warning(f"Could not generate embedding for task: {task_title}")
                return self._create_result(False, "Could not generate embedding")
            
            # Step 2: Find similar tasks from user's history
            # For now, we'll use a simplified approach since we don't have direct access to user's task history
            # In a real implementation, you would fetch the user's recent tasks from Notion
            similar_tasks = self._find_similar_tasks_from_history(task_title)
            
            if not similar_tasks:
                # No similar tasks found - create new activity
                return self._create_new_activity(task_title)
            
            # Step 3: Check if similar tasks belong to a known activity
            activity_id = self._find_activity_for_similar_tasks(similar_tasks)
            
            if activity_id:
                # Found existing activity - increment it
                return self._increment_existing_activity(activity_id, task_title)
            else:
                # Similar tasks found but no activity - create new activity
                return self._create_new_activity(task_title)
                
        except Exception as e:
            logger.error(f"Error processing new task: {e}")
            return self._create_result(False, f"Error: {str(e)}")
    
    def _find_similar_tasks_from_history(self, task_title: str) -> List[Dict[str, Any]]:
        """
        Find similar tasks from user's history using ChromaDB.
        
        Args:
            task_title: Current task title
            
        Returns:
            List[Dict[str, Any]]: List of similar tasks
        """
        try:
            # This is a simplified implementation
            # In a real scenario, you would:
            # 1. Fetch user's recent tasks from Notion
            # 2. Use ChromaDB to find similar ones
            # 3. Return the most similar tasks
            
            # For now, we'll return an empty list to simulate no similar tasks found
            # This will trigger the creation of a new activity
            logger.debug(f"Searching for similar tasks to: {task_title}")
            return []
            
        except Exception as e:
            logger.error(f"Error finding similar tasks: {e}")
            return []
    
    def _find_activity_for_similar_tasks(self, similar_tasks: List[Dict[str, Any]]) -> Optional[int]:
        """
        Find if similar tasks belong to a known activity.
        
        Args:
            similar_tasks: List of similar tasks
            
        Returns:
            Optional[int]: Activity ID if found, None otherwise
        """
        try:
            # Extract task IDs from similar tasks
            task_ids = [task.get('id') for task in similar_tasks if task.get('id')]
            
            if not task_ids:
                return None
            
            # Use the activity service to find the most likely activity
            activity_id = self.activity_service.find_most_likely_activity_for_tasks(
                self.user_id, task_ids
            )
            
            logger.debug(f"Found activity ID {activity_id} for {len(task_ids)} similar tasks")
            return activity_id
            
        except Exception as e:
            logger.error(f"Error finding activity for similar tasks: {e}")
            return None
    
    def _create_new_activity(self, task_title: str) -> Dict[str, Any]:
        """
        Create a new activity for the task.
        
        Args:
            task_title: Task title
            
        Returns:
            Dict[str, Any]: Result of activity creation
        """
        try:
            # Use AI to normalize the task title
            normalized_name = self._get_normalized_name(task_title)
            
            # Create new activity
            activity = self.activity_service.create_activity(
                self.user_id, normalized_name, task_title
            )
            
            logger.info(f"Created new activity: {normalized_name} for task: {task_title}")
            
            return self._create_result(
                True, 
                f"Created new activity: {normalized_name}",
                activity_id=activity.id,
                activity_name=normalized_name,
                is_new_activity=True
            )
            
        except Exception as e:
            logger.error(f"Error creating new activity: {e}")
            return self._create_result(False, f"Error creating activity: {str(e)}")
    
    def _increment_existing_activity(self, activity_id: int, task_title: str) -> Dict[str, Any]:
        """
        Increment an existing activity.
        
        Args:
            activity_id: Activity ID to increment
            task_title: New task title
            
        Returns:
            Dict[str, Any]: Result of activity increment
        """
        try:
            # Increment the activity
            activity = self.activity_service.increment_activity(activity_id, task_title)
            
            logger.info(f"Incremented activity {activity_id} to {activity.instance_count} instances")
            
            return self._create_result(
                True,
                f"Incremented activity: {activity.normalized_name}",
                activity_id=activity.id,
                activity_name=activity.normalized_name,
                instance_count=activity.instance_count,
                is_new_activity=False
            )
            
        except Exception as e:
            logger.error(f"Error incrementing activity: {e}")
            return self._create_result(False, f"Error incrementing activity: {str(e)}")
    
    def _get_normalized_name(self, task_title: str) -> str:
        """
        Use AI to normalize a task title into a clean activity name.
        
        Args:
            task_title: Original task title
            
        Returns:
            str: Normalized activity name
        """
        try:
            prompt = f"""Summarize this task title into a short, generic activity name of 2-4 words: '{task_title}'

Requirements:
- Use 2-4 words maximum
- Make it generic and reusable
- Focus on the core action/activity
- Use present tense
- Be consistent with similar activities

Examples:
- "Review weekly sales report" → "Weekly Sales Review"
- "Check email inbox" → "Email Check"
- "Update project documentation" → "Documentation Update"
- "Team standup meeting" → "Team Standup"

Activity name:"""

            response = get_ai_response(prompt)
            
            # Clean up the response
            normalized_name = response.strip()
            if len(normalized_name) > 50:  # Fallback if AI response is too long
                normalized_name = task_title[:50]
            
            logger.debug(f"Normalized '{task_title}' to '{normalized_name}'")
            return normalized_name
            
        except Exception as e:
            logger.error(f"Error normalizing task title: {e}")
            # Fallback to a simple truncation
            return task_title[:30] if len(task_title) > 30 else task_title
    
    def _create_result(self, success: bool, message: str, **kwargs) -> Dict[str, Any]:
        """
        Create a standardized result dictionary.
        
        Args:
            success: Whether the operation was successful
            message: Result message
            **kwargs: Additional result data
            
        Returns:
            Dict[str, Any]: Standardized result
        """
        result = {
            'success': success,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': self.user_id
        }
        result.update(kwargs)
        return result
    
    def get_user_activity_summary(self) -> Dict[str, Any]:
        """
        Get a summary of user's tracked activities.
        
        Returns:
            Dict[str, Any]: Activity summary
        """
        try:
            activities = self.activity_service.get_user_activities(self.user_id)
            stats = self.activity_service.get_activity_stats(self.user_id)
            
            summary = {
                'total_activities': len(activities),
                'stats': stats,
                'recent_activities': [
                    {
                        'name': activity.normalized_name,
                        'count': activity.instance_count,
                        'last_done': activity.last_instance_date.isoformat(),
                        'representative_tasks': activity.representative_tasks[:3]  # Show first 3
                    }
                    for activity in activities[:10]  # Show last 10 activities
                ]
            }
            
            logger.info(f"Generated activity summary for user {self.user_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error getting activity summary: {e}")
            return {'error': str(e)} 
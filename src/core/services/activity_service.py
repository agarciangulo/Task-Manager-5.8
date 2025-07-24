"""
Activity Data Service for managing tracked activities in the database.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from src.core.database.models import TrackedActivity
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ActivityDataService:
    """
    Service for managing tracked activities in the database.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the activity data service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
    
    def find_activity_by_name(self, user_id: str, normalized_name: str) -> Optional[TrackedActivity]:
        """
        Find an activity by user ID and normalized name.
        
        Args:
            user_id: User identifier
            normalized_name: Normalized activity name
            
        Returns:
            Optional[TrackedActivity]: Found activity or None
        """
        try:
            activity = self.db_session.query(TrackedActivity).filter(
                and_(
                    TrackedActivity.user_id == user_id,
                    TrackedActivity.normalized_name == normalized_name
                )
            ).first()
            
            logger.debug(f"Found activity for user {user_id}: {activity}")
            return activity
            
        except Exception as e:
            logger.error(f"Error finding activity by name: {e}")
            raise
    
    def create_activity(self, user_id: str, name: str, first_task_title: str) -> TrackedActivity:
        """
        Create a new tracked activity.
        
        Args:
            user_id: User identifier
            name: Normalized activity name
            first_task_title: Title of the first task for this activity
            
        Returns:
            TrackedActivity: Created activity
        """
        try:
            activity = TrackedActivity(
                user_id=user_id,
                normalized_name=name,
                instance_count=1,
                last_instance_date=datetime.utcnow(),
                representative_tasks=[first_task_title]
            )
            
            self.db_session.add(activity)
            self.db_session.commit()
            
            logger.info(f"Created new activity for user {user_id}: {name}")
            return activity
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creating activity: {e}")
            raise
    
    def increment_activity(self, activity_id: int, new_task_title: str) -> TrackedActivity:
        """
        Increment the instance count and update last instance date for an activity.
        
        Args:
            activity_id: Activity identifier
            new_task_title: Title of the new task
            
        Returns:
            TrackedActivity: Updated activity
        """
        try:
            activity = self.db_session.query(TrackedActivity).filter(
                TrackedActivity.id == activity_id
            ).first()
            
            if not activity:
                raise ValueError(f"Activity with ID {activity_id} not found")
            
            # Update activity
            activity.instance_count += 1
            activity.last_instance_date = datetime.utcnow()
            
            # Add new task to representative tasks (keep only last 10)
            if activity.representative_tasks is None:
                activity.representative_tasks = []
            
            activity.representative_tasks.append(new_task_title)
            if len(activity.representative_tasks) > 10:
                activity.representative_tasks = activity.representative_tasks[-10:]
            
            self.db_session.commit()
            
            logger.info(f"Incremented activity {activity_id} to {activity.instance_count} instances")
            return activity
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error incrementing activity: {e}")
            raise
    
    def find_most_likely_activity_for_tasks(self, user_id: str, task_ids: List[str]) -> Optional[int]:
        """
        Find the most common activity ID among a list of task IDs.
        This is a helper method that would need to query the main tasks table.
        
        Args:
            user_id: User identifier
            task_ids: List of task IDs to analyze
            
        Returns:
            Optional[int]: Most common activity ID or None
        """
        try:
            # This method would need to be implemented based on how tasks are stored
            # For now, we'll return None as this would require integration with the task storage
            # In a real implementation, you would:
            # 1. Query the tasks table for these task IDs
            # 2. Extract activity_id from each task
            # 3. Return the most common activity_id
            
            logger.debug(f"Finding most likely activity for {len(task_ids)} tasks")
            return None
            
        except Exception as e:
            logger.error(f"Error finding most likely activity: {e}")
            return None
    
    def get_user_activities(self, user_id: str) -> List[TrackedActivity]:
        """
        Get all tracked activities for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List[TrackedActivity]: List of user's activities
        """
        try:
            activities = self.db_session.query(TrackedActivity).filter(
                TrackedActivity.user_id == user_id
            ).order_by(TrackedActivity.last_instance_date.desc()).all()
            
            logger.debug(f"Found {len(activities)} activities for user {user_id}")
            return activities
            
        except Exception as e:
            logger.error(f"Error getting user activities: {e}")
            raise
    
    def get_activity_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user's tracked activities.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict[str, Any]: Activity statistics
        """
        try:
            # Get total activities
            total_activities = self.db_session.query(func.count(TrackedActivity.id)).filter(
                TrackedActivity.user_id == user_id
            ).scalar()
            
            # Get total instances
            total_instances = self.db_session.query(func.sum(TrackedActivity.instance_count)).filter(
                TrackedActivity.user_id == user_id
            ).scalar() or 0
            
            # Get most frequent activity
            most_frequent = self.db_session.query(TrackedActivity).filter(
                TrackedActivity.user_id == user_id
            ).order_by(TrackedActivity.instance_count.desc()).first()
            
            stats = {
                'total_activities': total_activities,
                'total_instances': total_instances,
                'most_frequent_activity': most_frequent.normalized_name if most_frequent else None,
                'most_frequent_count': most_frequent.instance_count if most_frequent else 0
            }
            
            logger.debug(f"Activity stats for user {user_id}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting activity stats: {e}")
            raise 
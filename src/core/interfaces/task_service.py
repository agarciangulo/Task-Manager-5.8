"""
Task service interface for AI Team Support.
Defines the contract for task management operations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class ITaskService(ABC):
    """Interface for task management operations."""
    
    @abstractmethod
    def extract_tasks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract tasks from freeform text."""
        pass
    
    @abstractmethod
    def process_user_update(self, text: str, user_id: str) -> Dict[str, Any]:
        """Process a user's text update and return results."""
        pass
    
    @abstractmethod
    def get_user_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a user."""
        pass
    
    @abstractmethod
    def create_task(self, user_id: str, task_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Create a new task for a user."""
        pass
    
    @abstractmethod
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update an existing task."""
        pass
    
    @abstractmethod
    def delete_task(self, task_id: str) -> Tuple[bool, str]:
        """Delete (archive) a task."""
        pass
    
    @abstractmethod
    def get_tasks_by_category(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get tasks grouped by category for a user."""
        pass
    
    @abstractmethod
    def get_stale_tasks(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get stale tasks for a user."""
        pass


class IUserService(ABC):
    """Interface for user management operations."""
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        pass
    
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Create a new user."""
        pass
    
    @abstractmethod
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update an existing user."""
        pass
    
    @abstractmethod
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate a user and return JWT token."""
        pass


class IInsightService(ABC):
    """Interface for AI insights and analysis."""
    
    @abstractmethod
    def generate_coaching_insights(self, user_id: str, tasks: List[Dict[str, Any]]) -> str:
        """Generate coaching insights for a user."""
        pass
    
    @abstractmethod
    def analyze_task_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze task patterns for a user."""
        pass
    
    @abstractmethod
    def get_project_insights(self, user_id: str, project_name: str) -> Dict[str, Any]:
        """Get insights for a specific project."""
        pass 
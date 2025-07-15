"""
Service container for AI Team Support.
Provides dependency injection and centralized service management.
"""
from typing import Optional
from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID, JWT_SECRET_KEY, JWT_ALGORITHM
from src.core.services.auth_service import AuthService
from src.core.services.task_management_service import TaskManagementService
from src.core.services.insight_service import InsightService
from src.core.security.jwt_utils import JWTManager


class ServiceContainer:
    """Container for managing service dependencies and instances."""
    
    def __init__(self):
        self._auth_service: Optional[AuthService] = None
        self._task_service: Optional[TaskManagementService] = None
        self._insight_service: Optional[InsightService] = None
        self._jwt_manager: Optional[JWTManager] = None
    
    @property
    def jwt_manager(self) -> JWTManager:
        """Get or create JWT manager instance."""
        if self._jwt_manager is None:
            self._jwt_manager = JWTManager(
                secret_key=JWT_SECRET_KEY,
                algorithm=JWT_ALGORITHM
            )
        return self._jwt_manager
    
    @property
    def auth_service(self) -> AuthService:
        """Get or create authentication service instance."""
        if self._auth_service is None:
            self._auth_service = AuthService(
                notion_token=NOTION_TOKEN,
                users_database_id=NOTION_USERS_DB_ID,
                jwt_manager=self.jwt_manager,
                parent_page_id=None  # Will be set when needed
            )
        return self._auth_service
    
    @property
    def task_service(self) -> TaskManagementService:
        """Get or create task management service instance."""
        if self._task_service is None:
            self._task_service = TaskManagementService(
                notion_token=NOTION_TOKEN,
                auth_service=self.auth_service
            )
        return self._task_service
    
    @property
    def insight_service(self) -> InsightService:
        """Get or create insight service instance."""
        if self._insight_service is None:
            self._insight_service = InsightService(
                notion_token=NOTION_TOKEN,
                auth_service=self.auth_service
            )
        return self._insight_service
    
    def reset(self):
        """Reset all service instances (useful for testing)."""
        self._auth_service = None
        self._task_service = None
        self._insight_service = None
        self._jwt_manager = None


# Global service container instance
service_container = ServiceContainer()


def get_task_service() -> TaskManagementService:
    """Get the task management service instance."""
    return service_container.task_service


def get_insight_service() -> InsightService:
    """Get the insight service instance."""
    return service_container.insight_service


def get_auth_service() -> AuthService:
    """Get the authentication service instance."""
    return service_container.auth_service


def get_jwt_manager() -> JWTManager:
    """Get the JWT manager instance."""
    return service_container.jwt_manager


def reset_services():
    """Reset all service instances (useful for testing)."""
    service_container.reset() 
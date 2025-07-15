"""
Service exceptions for AI Team Support.
Provides structured error handling for the service layer.
"""
from typing import Optional, Dict, Any


class ServiceError(Exception):
    """Base exception for all service errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class TaskServiceError(ServiceError):
    """Raised when task service operations fail."""
    pass


class TaskExtractionError(TaskServiceError):
    """Raised when task extraction fails."""
    pass


class TaskProcessingError(TaskServiceError):
    """Raised when task processing fails."""
    pass


class TaskValidationError(TaskServiceError):
    """Raised when task validation fails."""
    pass


class UserServiceError(ServiceError):
    """Raised when user service operations fail."""
    pass


class UserNotFoundError(UserServiceError):
    """Raised when a user is not found."""
    pass


class UserAuthenticationError(UserServiceError):
    """Raised when user authentication fails."""
    pass


class UserRegistrationError(UserServiceError):
    """Raised when user registration fails."""
    pass


class InsightServiceError(ServiceError):
    """Raised when insight service operations fail."""
    pass


class AIProcessingError(InsightServiceError):
    """Raised when AI processing fails."""
    pass


class NotionConnectionError(ServiceError):
    """Raised when Notion connection fails."""
    pass


class DatabaseError(ServiceError):
    """Raised when database operations fail."""
    pass


class ConfigurationError(ServiceError):
    """Raised when configuration is invalid or missing."""
    pass


class PluginError(ServiceError):
    """Raised when plugin operations fail."""
    pass


class EmailProcessingError(ServiceError):
    """Raised when email processing fails."""
    pass


class ValidationError(ServiceError):
    """Raised when data validation fails."""
    pass


class RateLimitError(ServiceError):
    """Raised when rate limits are exceeded."""
    pass


class ExternalServiceError(ServiceError):
    """Raised when external service calls fail."""
    pass 
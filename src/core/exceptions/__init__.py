"""
Exceptions package for AI Team Support.
This module provides structured error handling for the application.
"""
__version__ = "1.0.0"

# Import all exceptions for easy access
from .exceptions import (
    AgentError, NotionAgentError, TaskExtractionError, TaskExtractionAgentError,
    TaskProcessingError, TaskProcessingAgentError, EmbeddingAgentError,
    handle_agent_errors
)
from .service_exceptions import (
    ServiceError, TaskServiceError, TaskExtractionError, TaskProcessingError,
    TaskValidationError, UserServiceError, UserNotFoundError, UserAuthenticationError,
    UserRegistrationError, InsightServiceError, AIProcessingError, NotionConnectionError,
    DatabaseError, ConfigurationError, PluginError, EmailProcessingError,
    ValidationError, RateLimitError, ExternalServiceError
) 
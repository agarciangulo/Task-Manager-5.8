"""
Structured logging for AI Team Support service layer.
Provides consistent logging across all services.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps


class ServiceLogger:
    """Structured logging for service layer operations."""
    
    def __init__(self, service_name: str):
        self.logger = logging.getLogger(f"service.{service_name}")
        self.service_name = service_name
    
    def log_operation(self, operation: str, user_id: Optional[str] = None, **kwargs):
        """Log a service operation with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "operation": operation,
            "level": "INFO",
            **kwargs
        }
        
        if user_id:
            log_data["user_id"] = user_id
        
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, operation: str, error: Exception, user_id: Optional[str] = None, **kwargs):
        """Log an error with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "operation": operation,
            "level": "ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs
        }
        
        if user_id:
            log_data["user_id"] = user_id
        
        self.logger.error(json.dumps(log_data))
    
    def log_warning(self, operation: str, message: str, user_id: Optional[str] = None, **kwargs):
        """Log a warning with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "operation": operation,
            "level": "WARNING",
            "message": message,
            **kwargs
        }
        
        if user_id:
            log_data["user_id"] = user_id
        
        self.logger.warning(json.dumps(log_data))
    
    def log_performance(self, operation: str, duration_ms: float, user_id: Optional[str] = None, **kwargs):
        """Log performance metrics."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "operation": operation,
            "level": "INFO",
            "duration_ms": duration_ms,
            "metric_type": "performance",
            **kwargs
        }
        
        if user_id:
            log_data["user_id"] = user_id
        
        self.logger.info(json.dumps(log_data))


def log_operation(operation_name: str):
    """Decorator to automatically log service operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get logger from service instance
            logger = getattr(self, 'logger', None)
            if not logger:
                logger = ServiceLogger(self.__class__.__name__)
            
            # Extract user_id from kwargs or first argument if it's a user_id
            user_id = kwargs.get('user_id')
            if not user_id and args:
                # Try to extract user_id from first argument if it's a string
                if isinstance(args[0], str):
                    user_id = args[0]
            
            start_time = datetime.utcnow()
            
            try:
                # Log operation start
                logger.log_operation(
                    f"{operation_name}_start",
                    user_id=user_id,
                    args_count=len(args),
                    kwargs_keys=list(kwargs.keys())
                )
                
                # Execute the function
                result = func(self, *args, **kwargs)
                
                # Log operation success
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.log_operation(
                    f"{operation_name}_success",
                    user_id=user_id,
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                # Log operation error
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.log_error(
                    f"{operation_name}_error",
                    e,
                    user_id=user_id,
                    duration_ms=duration_ms
                )
                raise
        
        return wrapper
    return decorator


class LoggingMixin:
    """Mixin to add logging capabilities to services."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ServiceLogger(self.__class__.__name__)
    
    def log_info(self, operation: str, **kwargs):
        """Log an info message."""
        self.logger.log_operation(operation, **kwargs)
    
    def log_error(self, operation: str, error: Exception, **kwargs):
        """Log an error message."""
        self.logger.log_error(operation, error, **kwargs)
    
    def log_warning(self, operation: str, message: str, **kwargs):
        """Log a warning message."""
        self.logger.log_warning(operation, message, **kwargs) 
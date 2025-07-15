"""
Centralized logging configuration for the Task Manager application.
"""
import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG = LOGS_DIR / "app.log"
ERROR_LOG = LOGS_DIR / "error.log"
DEBUG_LOG = LOGS_DIR / "debug.log"

# Log formats
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and level.
    
    Args:
        name: The name of the logger (typically __name__)
        level: The logging level (default: INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    # Create formatters
    default_formatter = logging.Formatter(DEFAULT_FORMAT)
    detailed_formatter = logging.Formatter(DETAILED_FORMAT)
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(default_formatter)
    logger.addHandler(console_handler)
    
    # File handler for all logs (DEBUG and above)
    file_handler = logging.handlers.RotatingFileHandler(
        APP_LOG,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (ERROR and above)
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Debug file handler (DEBUG only)
    debug_handler = logging.handlers.RotatingFileHandler(
        DEBUG_LOG,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    # Add a filter to only show DEBUG level messages
    debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
    logger.addHandler(debug_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified name.
    This is the main function to use throughout the application.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(name)

# Create a default logger for the application
logger = get_logger("task_manager") 
class AgentError(Exception):
    """Base exception for all agent errors."""
    pass

class NotionAgentError(AgentError):
    pass

class TaskExtractionError(AgentError):
    pass

class TaskExtractionAgentError(AgentError):
    """Exception for task extraction agent errors."""
    pass

class TaskProcessingError(AgentError):
    pass

class TaskProcessingAgentError(AgentError):
    """Exception for task processing agent errors."""
    pass

class EmbeddingAgentError(AgentError):
    pass

import functools
import traceback
import logging

def handle_agent_errors(agent_name=None):
    """Decorator to standardize error handling for agent methods."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AgentError as e:
                logging.error(f"[{agent_name or func.__qualname__}] AgentError: {e}")
                return {"error": str(e), "type": type(e).__name__}
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"[{agent_name or func.__qualname__}] Unexpected error: {e}\n{tb}")
                return {"error": str(e), "type": "UnexpectedError", "traceback": tb}
        return wrapper
    return decorator 
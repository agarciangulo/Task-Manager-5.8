"""
Chat session management for Task Manager.
Handles maintaining conversation state for task verification.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

class ChatSession:
    """Manages chat session state for task verification."""
    
    def __init__(self, user_id):
        """
        Initialize the chat session.
        
        Args:
            user_id: Unique identifier for the user.
        """
        self.user_id = user_id
        self.context = {}
        self.last_activity = datetime.now()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def get_context(self):
        """Get the current context."""
        return self.context
    
    def set_context(self, context):
        """Set the current context."""
        self.context = context
        self.update_activity()
    
    def reset_context(self):
        """Reset the context."""
        self.context = {}
        self.update_activity()
    
    def is_expired(self, timeout_minutes=30):
        """Check if the session has expired."""
        return (datetime.now() - self.last_activity).total_seconds() > (timeout_minutes * 60)

class SessionManager:
    """Manages multiple chat sessions."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions = {}
    
    def get_session(self, user_id):
        """
        Get a session for a user, creating one if it doesn't exist.
        
        Args:
            user_id: Unique identifier for the user.
            
        Returns:
            ChatSession: The session for the user.
        """
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession(user_id)
        return self.sessions[user_id]
    
    def clean_expired_sessions(self, timeout_minutes=30):
        """
        Remove expired sessions.
        
        Args:
            timeout_minutes: Number of minutes after which a session is considered expired.
        """
        expired_sessions = []
        for user_id, session in self.sessions.items():
            if session.is_expired(timeout_minutes):
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            del self.sessions[user_id]
            
        return len(expired_sessions)
    
    def generate_user_id(self):
        """
        Generate a unique user ID.
        
        Returns:
            str: A unique user ID.
        """
        return str(uuid.uuid4())

# Global session manager instance
_session_manager = None

def get_session_manager():
    """
    Get the global session manager instance.
    
    Returns:
        SessionManager: The global session manager.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
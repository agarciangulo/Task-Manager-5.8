"""
Request models for AI Team Support API.
Provides structured input validation for API endpoints.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessUpdateRequest:
    """Request model for processing text updates."""
    text: str
    
    def validate(self) -> List[str]:
        """Validate the request data."""
        errors = []
        
        if not self.text or not self.text.strip():
            errors.append("Text content is required and cannot be empty")
        
        if len(self.text) > 10000:
            errors.append("Text content cannot exceed 10,000 characters")
        
        return errors


@dataclass
class CreateTaskRequest:
    """Request model for creating a new task."""
    task: str
    status: Optional[str] = "Not Started"
    employee: Optional[str] = ""
    category: Optional[str] = ""
    priority: Optional[str] = "Medium"
    date: Optional[str] = ""
    description: Optional[str] = ""
    
    def validate(self) -> List[str]:
        """Validate the request data."""
        errors = []
        
        if not self.task or not self.task.strip():
            errors.append("Task content is required and cannot be empty")
        
        if len(self.task) > 500:
            errors.append("Task content cannot exceed 500 characters")
        
        valid_statuses = ["Not Started", "In Progress", "Completed", "On Hold"]
        if self.status and self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        valid_priorities = ["Low", "Medium", "High", "Urgent"]
        if self.priority and self.priority not in valid_priorities:
            errors.append(f"Priority must be one of: {', '.join(valid_priorities)}")
        
        return errors


@dataclass
class UpdateTaskRequest:
    """Request model for updating an existing task."""
    task: Optional[str] = None
    status: Optional[str] = None
    employee: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Validate the request data."""
        errors = []
        
        if self.task and len(self.task) > 500:
            errors.append("Task content cannot exceed 500 characters")
        
        valid_statuses = ["Not Started", "In Progress", "Completed", "On Hold"]
        if self.status and self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        valid_priorities = ["Low", "Medium", "High", "Urgent"]
        if self.priority and self.priority not in valid_priorities:
            errors.append(f"Priority must be one of: {', '.join(valid_priorities)}")
        
        return errors


@dataclass
class LoginRequest:
    """Request model for user authentication."""
    email: str
    password: str
    
    def validate(self) -> List[str]:
        """Validate the request data."""
        errors = []
        
        if not self.email or not self.email.strip():
            errors.append("Email is required")
        
        if not self.password or not self.password.strip():
            errors.append("Password is required")
        
        if len(self.password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        return errors


@dataclass
class RegisterRequest:
    """Request model for user registration."""
    email: str
    password: str
    full_name: str
    company: Optional[str] = ""
    
    def validate(self) -> List[str]:
        """Validate the request data."""
        errors = []
        
        if not self.email or not self.email.strip():
            errors.append("Email is required")
        
        if not self.password or not self.password.strip():
            errors.append("Password is required")
        
        if len(self.password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        if not self.full_name or not self.full_name.strip():
            errors.append("Full name is required")
        
        return errors


@dataclass
class GetStaleTasksRequest:
    """Request model for getting stale tasks."""
    days: Optional[int] = 7
    
    def validate(self) -> List[str]:
        """Validate the request data."""
        errors = []
        
        if self.days and (self.days < 1 or self.days > 365):
            errors.append("Days must be between 1 and 365")
        
        return errors 
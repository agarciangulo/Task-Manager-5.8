"""
Response models for AI Team Support API.
Provides structured response formats for API endpoints.
"""
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class APIResponse:
    """Base API response model."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProcessUpdateResponse:
    """Response model for processing text updates."""
    success: bool
    message: str
    processed_tasks: List[Dict[str, Any]]
    insights: str
    summary: Dict[str, Any]
    log: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TaskResponse:
    """Response model for task operations."""
    id: str
    task: str
    status: str
    employee: str
    category: str
    priority: str
    date: str
    description: Optional[str] = None
    created_time: Optional[str] = None
    last_edited_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TaskListResponse:
    """Response model for task list operations."""
    tasks: List[TaskResponse]
    total_count: int
    filters: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['tasks'] = [task.to_dict() for task in self.tasks]
        return result


@dataclass
class TaskByCategoryResponse:
    """Response model for tasks grouped by category."""
    categories: Dict[str, List[Dict[str, Any]]]
    total_categories: int
    total_tasks: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class StaleTasksResponse:
    """Response model for stale tasks."""
    tasks: List[Dict[str, Any]]
    days_threshold: int
    total_stale_tasks: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class InsightResponse:
    """Response model for AI insights."""
    patterns: Dict[str, Any]
    recommendations: List[str]
    generated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProjectInsightResponse:
    """Response model for project-specific insights."""
    project_name: str
    project_insights: Dict[str, Any]
    recommendations: List[str]
    task_count: int
    completion_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AuthResponse:
    """Response model for authentication operations."""
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ErrorResponse:
    """Response model for error cases."""
    success: bool = False
    message: str = "An error occurred"
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


def create_success_response(data: Optional[Dict[str, Any]] = None, 
                          message: str = "Operation completed successfully") -> Dict[str, Any]:
    """Create a standardized success response."""
    return APIResponse(
        success=True,
        message=message,
        data=data
    ).to_dict()


def create_error_response(message: str, 
                        error_code: Optional[str] = None,
                        details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized error response."""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        details=details
    ).to_dict() 
"""
User model for authentication system.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class User:
    """User model representing a user in the system."""
    
    email: str
    password_hash: str
    full_name: str
    role: str
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True
    task_database_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'password_hash': self.password_hash,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'task_database_id': self.task_database_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user from dictionary representation."""
        return cls(
            user_id=data['user_id'],
            email=data['email'],
            password_hash=data['password_hash'],
            full_name=data['full_name'],
            role=data['role'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            is_active=data.get('is_active', True),
            task_database_id=data.get('task_database_id')
        )
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Convert user to public dictionary (without sensitive data)."""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'task_database_id': self.task_database_id
        }

"""
Authentication service for user management with Notion integration.
"""
import bcrypt
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from notion_client import Client

from src.core.models.user import User
from src.core.security.jwt_utils import JWTManager
from src.core.services.user_task_service import UserTaskService


class AuthService:
    """Service for handling user authentication and management."""
    
    def __init__(self, notion_token: str, users_database_id: str, jwt_manager: JWTManager, parent_page_id: str = None):
        """
        Initialize the authentication service.
        
        Args:
            notion_token: Notion API token.
            users_database_id: Notion database ID for users.
            jwt_manager: JWT manager instance.
            parent_page_id: Notion page ID where user task databases will be created.
        """
        self.notion_client = Client(auth=notion_token)
        self.users_database_id = users_database_id
        self.jwt_manager = jwt_manager
        self.parent_page_id = parent_page_id
        self.user_task_service = UserTaskService(notion_token)
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password.
            
        Returns:
            str: Hashed password.
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password.
            hashed_password: Hashed password to compare against.
            
        Returns:
            bool: True if password matches, False otherwise.
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _create_user_page(self, user: User) -> str:
        """
        Create a new user page in Notion.
        
        Args:
            user: User object to create.
            
        Returns:
            str: Notion page ID of the created user.
        """
        try:
            response = self.notion_client.pages.create(
                parent={"database_id": self.users_database_id},
                properties={
                    "Email": {
                        "title": [
                            {
                                "text": {
                                    "content": user.email
                                }
                            }
                        ]
                    },
                    "UserID": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user.user_id
                                }
                            }
                        ]
                    },
                    "PasswordHash": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user.password_hash
                                }
                            }
                        ]
                    },
                    "FullName": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user.full_name
                                }
                            }
                        ]
                    },
                    "Role": {
                        "select": {
                            "name": user.role
                        }
                    },
                    "CreatedAt": {
                        "date": {
                            "start": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
                        }
                    },
                    "IsActive": {
                        "checkbox": user.is_active
                    },
                    "TaskDatabaseID": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user.task_database_id or ""
                                }
                            }
                        ]
                    }
                }
            )
            return response["id"]
        except Exception as e:
            raise Exception(f"Failed to create user in Notion: {str(e)}")
    
    def _update_user_page(self, page_id: str, updates: Dict[str, Any]) -> None:
        """
        Update a user page in Notion.
        
        Args:
            page_id: Notion page ID of the user.
            updates: Dictionary of properties to update.
        """
        try:
            properties = {}
            
            if "email" in updates:
                properties["Email"] = {
                    "title": [
                        {
                            "text": {
                                "content": updates["email"]
                            }
                        }
                    ]
                }
            
            if "password_hash" in updates:
                properties["PasswordHash"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": updates["password_hash"]
                            }
                        }
                    ]
                }
            
            if "full_name" in updates:
                properties["FullName"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": updates["full_name"]
                            }
                        }
                    ]
                }
            
            if "role" in updates:
                properties["Role"] = {
                    "select": {
                        "name": updates["role"]
                    }
                }
            
            if "last_login" in updates:
                properties["LastLogin"] = {
                    "date": {
                        "start": updates["last_login"].isoformat()
                    }
                }
            
            if "is_active" in updates:
                properties["IsActive"] = {
                    "checkbox": updates["is_active"]
                }
            
            if "updated_at" in updates:
                properties["UpdatedAt"] = {
                    "date": {
                        "start": updates["updated_at"].isoformat()
                    }
                }
            
            if "task_database_id" in updates:
                properties["TaskDatabaseID"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": updates["task_database_id"]
                            }
                        }
                    ]
                }
            
            if properties:
                self.notion_client.pages.update(page_id=page_id, properties=properties)
                
        except Exception as e:
            raise Exception(f"Failed to update user in Notion: {str(e)}")
    
    def _get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email from Notion.
        
        Args:
            email: The user's email address.
            
        Returns:
            Optional[User]: User object if found, None otherwise.
        """
        try:
            response = self.notion_client.databases.query(
                database_id=self.users_database_id,
                filter={
                    "property": "Email",
                    "title": {
                        "equals": email
                    }
                }
            )
            
            if not response["results"]:
                return None
            
            page = response["results"][0]
            properties = page["properties"]
            
            # Extract user data from Notion properties
            user_data = {
                "email": self._extract_title(properties["Email"]),
                "user_id": self._extract_rich_text(properties["UserID"]),
                "password_hash": self._extract_rich_text(properties["PasswordHash"]),
                "full_name": self._extract_rich_text(properties["FullName"]),
                "role": self._extract_select(properties["Role"]),
                "created_at": self._extract_date(properties.get("CreatedAt")),
                "updated_at": self._extract_date(properties.get("UpdatedAt")),
                "last_login": self._extract_date(properties.get("LastLogin")),
                "is_active": self._extract_checkbox(properties.get("IsActive", {})),
                "task_database_id": self._extract_rich_text(properties.get("TaskDatabaseID", {}))
            }
            
            return User(**user_data)
            
        except Exception as e:
            raise Exception(f"Failed to get user from Notion: {str(e)}")
    
    def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by their internal UserID from Notion.
        
        Args:
            user_id: The user's internal ID (UUID).
            
        Returns:
            Optional[User]: User object if found, None otherwise.
        """
        try:
            response = self.notion_client.databases.query(
                database_id=self.users_database_id,
                filter={
                    "property": "UserID",
                    "rich_text": {
                        "equals": user_id
                    }
                }
            )
            
            if not response["results"]:
                return None
            
            page = response["results"][0]
            properties = page["properties"]
            
            # Extract user data from Notion properties
            user_data = {
                "email": self._extract_title(properties["Email"]),
                "user_id": self._extract_rich_text(properties["UserID"]),
                "password_hash": self._extract_rich_text(properties["PasswordHash"]),
                "full_name": self._extract_rich_text(properties["FullName"]),
                "role": self._extract_select(properties["Role"]),
                "created_at": self._extract_date(properties.get("CreatedAt")),
                "updated_at": self._extract_date(properties.get("UpdatedAt")),
                "last_login": self._extract_date(properties.get("LastLogin")),
                "is_active": self._extract_checkbox(properties.get("IsActive", {})),
                "task_database_id": self._extract_rich_text(properties.get("TaskDatabaseID", {}))
            }
            
            return User(**user_data)
            
        except Exception as e:
            raise Exception(f"Failed to get user from Notion: {str(e)}")
    
    def _get_all_users(self) -> List[User]:
        """
        Get all users from Notion.
        
        Returns:
            List[User]: List of all users.
        """
        try:
            response = self.notion_client.databases.query(
                database_id=self.users_database_id
            )
            
            users = []
            for page in response["results"]:
                properties = page["properties"]
                
                user_data = {
                    "email": self._extract_title(properties["Email"]),
                    "user_id": self._extract_rich_text(properties["UserID"]),
                    "password_hash": self._extract_rich_text(properties["PasswordHash"]),
                    "full_name": self._extract_rich_text(properties["FullName"]),
                    "role": self._extract_select(properties["Role"]),
                    "created_at": self._extract_date(properties.get("CreatedAt")),
                    "updated_at": self._extract_date(properties.get("UpdatedAt")),
                    "last_login": self._extract_date(properties.get("LastLogin")),
                    "is_active": self._extract_checkbox(properties.get("IsActive", {})),
                    "task_database_id": self._extract_rich_text(properties.get("TaskDatabaseID", {}))
                }
                
                users.append(User(**user_data))
            
            return users
            
        except Exception as e:
            raise Exception(f"Failed to get users from Notion: {str(e)}")
    
    def _extract_title(self, property_data: Dict[str, Any]) -> str:
        """Extract title from Notion property."""
        title_array = property_data.get("title", [])
        if not title_array:
            return ""
        return title_array[0].get("text", {}).get("content", "")
    
    def _extract_rich_text(self, property_data: Dict[str, Any]) -> str:
        """Extract rich text from Notion property."""
        rich_text_array = property_data.get("rich_text", [])
        if not rich_text_array:
            return ""
        return rich_text_array[0].get("text", {}).get("content", "")
    
    def _extract_select(self, property_data: Dict[str, Any]) -> str:
        """Extract select value from Notion property."""
        select_obj = property_data.get("select")
        if not select_obj:
            return ""
        return select_obj.get("name", "")
    
    def _extract_date(self, property_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract date from Notion property."""
        if not property_data:
            return None
        date_obj = property_data.get("date")
        if not date_obj:
            return None
        date_str = date_obj.get("start")
        if date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return None
    
    def _extract_checkbox(self, property_data: Dict[str, Any]) -> bool:
        """Extract checkbox value from Notion property."""
        if not property_data:
            return True  # Default to True if property doesn't exist
        return property_data.get("checkbox", True)
    
    def register_user(self, email: str, password: str, full_name: str, role: str = "user") -> User:
        """
        Register a new user.
        
        Args:
            email: The user's email address.
            password: Plain text password.
            full_name: The user's full name.
            role: The user's role (default: "user").
            
        Returns:
            User: The created user object.
            
        Raises:
            ValueError: If user already exists or validation fails.
        """
        # Check if user already exists
        existing_user = self._get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Validate input
        if not email or not password or not full_name:
            raise ValueError("Email, password, and full name are required")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Create user object
        user = User(
            email=email,
            password_hash=self._hash_password(password),
            full_name=full_name,
            role=role,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        # Create user in Notion
        self._create_user_page(user)
        
        # Create task database for the user if parent page is configured
        if self.parent_page_id:
            try:
                task_database_id = self.user_task_service.create_user_task_database(user, self.parent_page_id)
                user.task_database_id = task_database_id
                
                # Update user in Notion with task database ID
                user_page = self._get_notion_page_by_email(email)
                if user_page:
                    self._update_user_page(user_page['id'], {"task_database_id": task_database_id})
                    
            except Exception as e:
                print(f"Warning: Failed to create task database for user {email}: {str(e)}")
                # Don't fail registration if task database creation fails
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """
        Authenticate a user and return JWT token.
        
        Args:
            email: The user's email address.
            password: Plain text password.
            
        Returns:
            Optional[str]: JWT token if authentication successful, None otherwise.
        """
        try:
            # Get user from database
            user = self._get_user_by_email(email)
            if not user:
                return None
            
            # Check if user is active
            if not user.is_active:
                return None
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                return None
            
            # Update last login
            page = self._get_notion_page_by_email(email)
            if page:
                user.last_login = datetime.utcnow()
                self._update_user_page(page['id'], {"last_login": user.last_login})
            
            # Generate JWT token
            token = self.jwt_manager.generate_token(user.user_id, user.role, user.email)
            
            return token
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by their internal ID (UUID).
        
        Args:
            user_id: The user's internal ID.
            
        Returns:
            Optional[User]: User object if found, None otherwise.
        """
        return self._get_user_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address.
        
        Args:
            email: The user's email address.
            
        Returns:
            Optional[User]: User object if found, None otherwise.
        """
        return self._get_user_by_email(email)
    
    def get_all_users(self) -> List[User]:
        """
        Get all users.
        
        Returns:
            List[User]: List of all users.
        """
        return self._get_all_users()
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update a user's information.
        
        Args:
            user_id: The user's internal ID (UUID).
            updates: Dictionary of fields to update.
            
        Returns:
            Optional[User]: Updated user object if successful, None otherwise.
        """
        try:
            user_page = self._get_notion_page_by_id(user_id)
            if not user_page:
                return None
            
            # Handle password updates
            if "password" in updates:
                if len(updates["password"]) < 8:
                    raise ValueError("Password must be at least 8 characters long")
                updates["password_hash"] = self._hash_password(updates.pop("password"))
            
            # Update user object
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            updates['updated_at'] = user.updated_at
            
            # Update in Notion
            self._update_user_page(user_page['id'], updates)

            # Re-fetch user to get the updated object
            return self._get_user_by_id(user_id)
            
        except Exception as e:
            print(f"Update user error: {str(e)}")
            return None
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user.
        
        Args:
            user_id: The user's internal ID (UUID).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            user_page = self._get_notion_page_by_id(user_id)
            if not user_page:
                return False
            
            updates = {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }
            
            self._update_user_page(user_page['id'], updates)
            
            return True
            
        except Exception as e:
            print(f"Deactivate user error: {str(e)}")
            return False
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and return user info.
        
        Args:
            token: The JWT token to validate.
            
        Returns:
            Optional[Dict[str, Any]]: Token payload if valid, None otherwise.
        """
        try:
            payload = self.jwt_manager.decode_token(token)
            
            # Check if user still exists and is active
            user = self._get_user_by_id(payload['user_id'])
            if not user or not user.is_active:
                return None
            
            return payload
            
        except Exception:
            return None
    
    def _get_notion_page_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Helper to get the raw Notion page for a user by email."""
        try:
            response = self.notion_client.databases.query(
                database_id=self.users_database_id,
                filter={
                    "property": "Email",
                    "title": {
                        "equals": email
                    }
                }
            )
            return response["results"][0] if response["results"] else None
        except Exception:
            return None

    def _get_notion_page_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Helper to get the raw Notion page for a user by UserID."""
        try:
            response = self.notion_client.databases.query(
                database_id=self.users_database_id,
                filter={
                    "property": "UserID",
                    "rich_text": {
                        "equals": user_id
                    }
                }
            )
            return response["results"][0] if response["results"] else None
        except Exception:
            return None 
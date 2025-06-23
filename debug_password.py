#!/usr/bin/env python3
"""
Debug password hashing and verification for authentication system.
"""

import os
import bcrypt
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def test_password_hashing():
    """Test password hashing functionality."""
    print("🔍 Testing password hashing...")
    
    test_password = "testpassword123"
    
    # Hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(test_password.encode('utf-8'), salt)
    hashed_str = hashed_password.decode('utf-8')
    
    print(f"Original password: {test_password}")
    print(f"Hashed password: {hashed_str}")
    
    # Verify the password
    is_valid = bcrypt.checkpw(test_password.encode('utf-8'), hashed_password)
    print(f"Password verification: {is_valid}")
    
    return hashed_str

def check_notion_user_data():
    """Check what's stored in Notion for the test user."""
    print("\n🔍 Checking Notion user data...")
    
    notion_token = os.getenv('NOTION_TOKEN')
    users_db_id = os.getenv('NOTION_USERS_DB_ID')
    
    try:
        client = Client(auth=notion_token)
        
        # Query for the test user
        response = client.databases.query(
            database_id=users_db_id,
            filter={
                "property": "UserID",
                "title": {
                    "contains": "debug_user"
                }
            }
        )
        
        if response["results"]:
            user_page = response["results"][0]
            properties = user_page["properties"]
            
            print("📋 User data in Notion:")
            print(f"  UserID: {properties['UserID']['title'][0]['text']['content']}")
            print(f"  FullName: {properties['FullName']['rich_text'][0]['text']['content']}")
            print(f"  Role: {properties['Role']['select']['name']}")
            
            # Check password hash
            password_hash = properties['PasswordHash']['rich_text'][0]['text']['content']
            print(f"  PasswordHash: {password_hash[:20]}...")
            
            # Test password verification
            test_password = "testpassword123"
            try:
                is_valid = bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8'))
                print(f"  Password verification test: {is_valid}")
            except Exception as e:
                print(f"  Password verification error: {str(e)}")
            
            return password_hash
        else:
            print("❌ No test user found in Notion")
            return None
            
    except Exception as e:
        print(f"❌ Error checking Notion data: {str(e)}")
        return None

def test_auth_service_password():
    """Test the auth service password methods directly."""
    print("\n🔍 Testing auth service password methods...")
    
    try:
        from core.services.auth_service import AuthService
        from core.security.jwt_utils import JWTManager
        
        # Initialize components
        jwt_manager = JWTManager()
        auth_service = AuthService(
            os.getenv('NOTION_TOKEN'),
            os.getenv('NOTION_USERS_DB_ID'),
            jwt_manager
        )
        
        # Test password hashing
        test_password = "testpassword123"
        hashed = auth_service._hash_password(test_password)
        print(f"Auth service hash: {hashed[:20]}...")
        
        # Test password verification
        is_valid = auth_service._verify_password(test_password, hashed)
        print(f"Auth service verification: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth service test error: {str(e)}")
        return False

def main():
    """Run all password debugging tests."""
    print("🔧 Password Debugging")
    print("=" * 40)
    
    # Test 1: Basic password hashing
    test_hash = test_password_hashing()
    
    # Test 2: Check Notion data
    notion_hash = check_notion_user_data()
    
    # Test 3: Auth service methods
    auth_service_ok = test_auth_service_password()
    
    print("\n📊 Summary:")
    print(f"  Basic hashing: ✅ Working")
    print(f"  Notion data: {'✅ Found' if notion_hash else '❌ Not found'}")
    print(f"  Auth service: {'✅ Working' if auth_service_ok else '❌ Error'}")

if __name__ == "__main__":
    main() 
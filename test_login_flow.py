#!/usr/bin/env python3
"""
Test the complete login flow step by step.
"""

import os
from dotenv import load_dotenv
from core.services.auth_service import AuthService
from core.security.jwt_utils import JWTManager

# Load environment variables
load_dotenv()

def test_login_flow():
    """Test the complete login flow."""
    print("🔍 Testing complete login flow...")
    
    # Initialize auth service
    jwt_manager = JWTManager()
    auth_service = AuthService(
        os.getenv('NOTION_TOKEN'),
        os.getenv('NOTION_USERS_DB_ID'),
        jwt_manager
    )
    
    # Test user credentials
    user_id = "debug_user_20250619_185034"  # From previous test
    password = "testpassword123"
    
    print(f"Testing login for user: {user_id}")
    
    # Step 1: Get user from database
    print("\n1. Getting user from database...")
    try:
        user = auth_service.get_user_by_id(user_id)
        if user:
            print(f"   ✅ User found: {user.full_name}")
            print(f"   Role: {user.role}")
            print(f"   Is active: {user.is_active}")
        else:
            print("   ❌ User not found")
            return False
    except Exception as e:
        print(f"   ❌ Error getting user: {str(e)}")
        return False
    
    # Step 2: Verify password
    print("\n2. Verifying password...")
    try:
        is_valid = auth_service._verify_password(password, user.password_hash)
        print(f"   Password verification: {is_valid}")
        if not is_valid:
            print("   ❌ Password verification failed")
            return False
    except Exception as e:
        print(f"   ❌ Error verifying password: {str(e)}")
        return False
    
    # Step 3: Generate token
    print("\n3. Generating JWT token...")
    try:
        token = jwt_manager.generate_token(user.user_id, user.role)
        print(f"   ✅ Token generated: {token[:20]}...")
    except Exception as e:
        print(f"   ❌ Error generating token: {str(e)}")
        return False
    
    # Step 4: Test complete authentication
    print("\n4. Testing complete authentication...")
    try:
        auth_token = auth_service.authenticate_user(user_id, password)
        if auth_token:
            print(f"   ✅ Authentication successful!")
            print(f"   Token: {auth_token[:20]}...")
            return True
        else:
            print("   ❌ Authentication failed")
            return False
    except Exception as e:
        print(f"   ❌ Error in authentication: {str(e)}")
        return False

def test_user_retrieval():
    """Test user retrieval from Notion."""
    print("\n🔍 Testing user retrieval from Notion...")
    
    try:
        from notion_client import Client
        
        client = Client(auth=os.getenv('NOTION_TOKEN'))
        
        # Query for the test user
        response = client.databases.query(
            database_id=os.getenv('NOTION_USERS_DB_ID'),
            filter={
                "property": "UserID",
                "title": {
                    "equals": "debug_user_20250619_185034"
                }
            }
        )
        
        if response["results"]:
            user_page = response["results"][0]
            properties = user_page["properties"]
            
            print("   ✅ User found in Notion")
            print(f"   UserID: {properties['UserID']['title'][0]['text']['content']}")
            print(f"   FullName: {properties['FullName']['rich_text'][0]['text']['content']}")
            print(f"   Role: {properties['Role']['select']['name']}")
            print(f"   IsActive: {properties['IsActive']['checkbox']}")
            
            return True
        else:
            print("   ❌ User not found in Notion")
            return False
            
    except Exception as e:
        print(f"   ❌ Error querying Notion: {str(e)}")
        return False

def main():
    """Run all login flow tests."""
    print("🔧 Login Flow Testing")
    print("=" * 40)
    
    # Test 1: User retrieval from Notion
    notion_ok = test_user_retrieval()
    
    # Test 2: Complete login flow
    login_ok = test_login_flow()
    
    print("\n📊 Summary:")
    print(f"  Notion retrieval: {'✅ Working' if notion_ok else '❌ Failed'}")
    print(f"  Login flow: {'✅ Working' if login_ok else '❌ Failed'}")
    
    if login_ok:
        print("\n🎉 Login flow is working correctly!")
        print("The issue might be in the Flask route or request handling.")
    else:
        print("\n🔍 Login flow has issues. Check the error messages above.")

if __name__ == "__main__":
    main() 
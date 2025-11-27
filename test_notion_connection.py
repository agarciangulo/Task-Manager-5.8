#!/usr/bin/env python3
"""
Simple test: Can auth_service connect to Notion and find a user?
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_user_lookup():
    """Test if we can look up a user from Notion."""
    print("=" * 60)
    print("TEST: Notion Connection & User Lookup")
    print("=" * 60)
    
    try:
        from src.core.services.auth_service import AuthService
        from src.core.security.jwt_utils import JWTManager
        from src.config.settings import NOTION_TOKEN, NOTION_USERS_DB_ID
        
        test_email = os.getenv('GMAIL_ADDRESS', 'andres.garcia.angulo@gmail.com')
        
        print(f"\n1. Initializing AuthService...")
        jwt_manager = JWTManager(secret_key="dummy", algorithm="HS256")
        auth_service = AuthService(NOTION_TOKEN, NOTION_USERS_DB_ID, jwt_manager, None)
        print("   ✅ AuthService created")
        
        print(f"\n2. Looking up user: {test_email}...")
        user = auth_service.get_user_by_email(test_email)
        
        if user:
            print(f"   ✅ User found!")
            print(f"      - Name: {user.full_name}")
            print(f"      - Task Database ID: {user.task_database_id}")
            print(f"      - Active: {user.is_active}")
            return True
        else:
            print(f"   ❌ User not found")
            print(f"      Register {test_email} in Notion users database")
            return False
            
    except AttributeError as e:
        if 'query' in str(e):
            print(f"   ❌ Still using old databases.query() method")
            print(f"   The fix needs /v1/ prefix in the path")
            return False
        else:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing Notion Connection\n")
    success = test_user_lookup()
    
    if success:
        print("\n✅ Connection works! The fix is correct.")
        sys.exit(0)
    else:
        print("\n❌ Connection failed. Check the error above.")
        sys.exit(1)






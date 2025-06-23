#!/usr/bin/env python3
"""
Setup script for environment variables required by the authentication system.
"""

import os
from dotenv import load_dotenv

def main():
    """Check and help set up required environment variables."""
    print("🔧 Authentication System Environment Setup")
    print("=" * 50)
    
    # Load existing .env file if it exists
    load_dotenv()
    
    # Required variables for authentication
    required_vars = {
        'JWT_SECRET_KEY': 'Secret key for JWT token signing',
        'NOTION_USERS_DB_ID': 'Notion database ID for storing users',
        'NOTION_TOKEN': 'Notion API token',
        'NOTION_DATABASE_ID': 'Notion database ID for tasks',
        'NOTION_FEEDBACK_DB_ID': 'Notion database ID for feedback',
        'GEMINI_API_KEY': 'Google Gemini API key'
    }
    
    # Optional variables
    optional_vars = {
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRATION_HOURS': '24',
        'ENABLE_AUTHENTICATION': 'True',
        'DEBUG_MODE': 'False'
    }
    
    print("\n📋 Required Environment Variables:")
    print("-" * 40)
    
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show first 8 characters for security
            display_value = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: MISSING - {description}")
            missing_required.append(var)
    
    print("\n📋 Optional Environment Variables:")
    print("-" * 40)
    
    for var, default_value in optional_vars.items():
        value = os.getenv(var, default_value)
        print(f"⚙️  {var}: {value}")
    
    if missing_required:
        print(f"\n🚨 Missing {len(missing_required)} required environment variables!")
        print("\n📝 To fix this, add the following to your .env file:")
        print("-" * 50)
        
        for var in missing_required:
            if var == 'JWT_SECRET_KEY':
                print(f"{var}=your-jwt-secret-key-here")
            elif var == 'NOTION_USERS_DB_ID':
                print(f"{var}=your-notion-users-database-id")
            elif var == 'NOTION_TOKEN':
                print(f"{var}=your-notion-api-token")
            elif var == 'NOTION_DATABASE_ID':
                print(f"{var}=your-notion-tasks-database-id")
            elif var == 'NOTION_FEEDBACK_DB_ID':
                print(f"{var}=your-notion-feedback-database-id")
            elif var == 'GEMINI_API_KEY':
                print(f"{var}=your-gemini-api-key")
        
        print("\n💡 Quick setup:")
        print("1. Generate JWT key: python generate_jwt_key.py")
        print("2. Create Notion users database and get its ID")
        print("3. Get your Notion API token from https://www.notion.so/my-integrations")
        print("4. Add all variables to your .env file")
        
        return False
    else:
        print("\n✅ All required environment variables are set!")
        print("🚀 You can now run: python app_auth.py")
        return True

if __name__ == "__main__":
    main() 
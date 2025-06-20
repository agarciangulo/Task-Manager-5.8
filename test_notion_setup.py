#!/usr/bin/env python3
"""
Test Notion database setup for authentication system.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def test_notion_connection():
    """Test basic Notion connection."""
    print("🔍 Testing Notion connection...")
    
    notion_token = os.getenv('NOTION_TOKEN')
    users_db_id = os.getenv('NOTION_USERS_DB_ID')
    
    if not notion_token:
        print("❌ NOTION_TOKEN not found in environment variables")
        return False
    
    if not users_db_id:
        print("❌ NOTION_USERS_DB_ID not found in environment variables")
        return False
    
    try:
        client = Client(auth=notion_token)
        
        # Test connection by getting database info
        database = client.databases.retrieve(database_id=users_db_id)
        print(f"✅ Connected to database: {database['title'][0]['text']['content']}")
        return True
        
    except Exception as e:
        print(f"❌ Notion connection failed: {str(e)}")
        return False

def test_database_structure():
    """Test if database has required columns."""
    print("\n🔍 Testing database structure...")
    
    notion_token = os.getenv('NOTION_TOKEN')
    users_db_id = os.getenv('NOTION_USERS_DB_ID')
    
    try:
        client = Client(auth=notion_token)
        database = client.databases.retrieve(database_id=users_db_id)
        
        properties = database['properties']
        required_columns = ['UserID', 'PasswordHash', 'FullName', 'Role']
        
        print("📋 Database columns found:")
        for column_name in properties.keys():
            column_type = properties[column_name]['type']
            print(f"  - {column_name} ({column_type})")
        
        print("\n📋 Required columns:")
        missing_columns = []
        for column in required_columns:
            if column in properties:
                print(f"  ✅ {column}")
            else:
                print(f"  ❌ {column} - MISSING")
                missing_columns.append(column)
        
        if missing_columns:
            print(f"\n🚨 Missing {len(missing_columns)} required columns!")
            print("Please add these columns to your Notion database:")
            for column in missing_columns:
                if column == 'UserID':
                    print(f"  - {column}: Title type")
                elif column == 'PasswordHash':
                    print(f"  - {column}: Text type")
                elif column == 'FullName':
                    print(f"  - {column}: Text type")
                elif column == 'Role':
                    print(f"  - {column}: Select type (options: user, admin)")
            return False
        else:
            print("\n✅ All required columns are present!")
            return True
            
    except Exception as e:
        print(f"❌ Database structure test failed: {str(e)}")
        return False

def main():
    """Run all Notion setup tests."""
    print("🔧 Notion Database Setup Test")
    print("=" * 40)
    
    # Test 1: Connection
    if not test_notion_connection():
        print("\n❌ Cannot connect to Notion. Check your NOTION_TOKEN.")
        return False
    
    # Test 2: Database structure
    if not test_database_structure():
        print("\n❌ Database structure is incorrect. Please fix the missing columns.")
        return False
    
    print("\n✅ All Notion setup tests passed!")
    print("🚀 Your Notion database is ready for the authentication system!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 
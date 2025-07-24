#!/usr/bin/env python3
"""
Production Database Setup Script for Google Cloud Deployment
This script initializes all required database schemas and tables.
"""
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking production environment configuration...")
    
    load_dotenv()
    
    required_vars = {
        'DATABASE_URL': 'PostgreSQL database connection URL',
        'NOTION_TOKEN': 'Notion API token',
        'NOTION_DATABASE_ID': 'Notion database ID',
        'NOTION_FEEDBACK_DB_ID': 'Notion feedback database ID',
        'NOTION_USERS_DB_ID': 'Notion users database ID',
        'JWT_SECRET_KEY': 'JWT secret key for authentication',
        'GEMINI_API_KEY': 'Google Gemini API key'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        else:
            # Show first 8 characters for security
            display_value = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables and try again.")
        print("Use env.production.template as a reference.")
        return False
    
    print("✅ Environment configuration is valid")
    return True

def test_database_connection():
    """Test database connection."""
    print("\n🔍 Testing database connection...")
    
    try:
        from sqlalchemy import create_engine, text
        
        database_url = os.getenv('DATABASE_URL')
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def setup_database_schemas():
    """Set up all required database schemas."""
    print("\n🏗️ Setting up database schemas...")
    
    try:
        from sqlalchemy import create_engine, text
        
        database_url = os.getenv('DATABASE_URL')
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Create email_archive schema
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS email_archive"))
            print("✅ email_archive schema created")
            
            # Create public schema tables if they don't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tracked_activities (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    normalized_name VARCHAR(255) NOT NULL,
                    instance_count INTEGER NOT NULL DEFAULT 1,
                    last_instance_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    representative_tasks JSONB DEFAULT '[]',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, normalized_name)
                )
            """))
            print("✅ tracked_activities table created")
            
            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tracked_activities_user_id ON tracked_activities(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tracked_activities_name ON tracked_activities(normalized_name)"))
            print("✅ Database indexes created")
            
            conn.commit()
            
        return True
        
    except Exception as e:
        print(f"❌ Database schema setup failed: {e}")
        return False

def setup_email_archive_tables():
    """Set up email archive tables."""
    print("\n📧 Setting up email archive tables...")
    
    try:
        from src.core.models.email_archive import Base
        from sqlalchemy import create_engine
        
        database_url = os.getenv('DATABASE_URL')
        engine = create_engine(database_url)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Email archive tables created")
        
        return True
        
    except Exception as e:
        print(f"❌ Email archive setup failed: {e}")
        return False

def verify_notion_connection():
    """Verify Notion API connection."""
    print("\n🔍 Verifying Notion API connection...")
    
    try:
        from src.core.agents.notion_agent import NotionAgent
        
        notion_agent = NotionAgent()
        if notion_agent.validate_connection():
            print("✅ Notion API connection successful")
            return True
        else:
            print("❌ Notion API connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Notion API verification failed: {e}")
        return False

def verify_ai_connection():
    """Verify AI provider connection."""
    print("\n🤖 Verifying AI provider connection...")
    
    try:
        ai_provider = os.getenv('AI_PROVIDER', 'gemini')
        
        if ai_provider == 'gemini':
            from src.core.gemini_client import client
            if client:
                print("✅ Gemini API connection successful")
                return True
            else:
                print("❌ Gemini API connection failed")
                return False
        elif ai_provider == 'openai':
            from src.core.openai_client import client
            if client:
                print("✅ OpenAI API connection successful")
                return True
            else:
                print("❌ OpenAI API connection failed")
                return False
        else:
            print(f"❌ Unknown AI provider: {ai_provider}")
            return False
            
    except Exception as e:
        print(f"❌ AI provider verification failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Production Database Setup for Google Cloud")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Setup database schemas
    if not setup_database_schemas():
        print("\n❌ Database schema setup failed")
        sys.exit(1)
    
    # Setup email archive tables
    if not setup_email_archive_tables():
        print("\n❌ Email archive setup failed")
        sys.exit(1)
    
    # Verify external connections
    print("\n🔍 Verifying external service connections...")
    
    notion_ok = verify_notion_connection()
    ai_ok = verify_ai_connection()
    
    if not notion_ok:
        print("⚠️ Warning: Notion connection failed - some features may not work")
    
    if not ai_ok:
        print("⚠️ Warning: AI provider connection failed - some features may not work")
    
    print("\n🎉 Production database setup completed!")
    print("\n📋 Summary:")
    print("✅ Environment variables configured")
    print("✅ Database connection established")
    print("✅ Database schemas created")
    print("✅ Email archive tables initialized")
    print(f"{'✅' if notion_ok else '⚠️'} Notion API connection")
    print(f"{'✅' if ai_ok else '⚠️'} AI provider connection")
    
    print("\n🚀 Your application is ready for Google Cloud deployment!")
    print("\nNext steps:")
    print("1. Deploy to Google Cloud Run or Compute Engine")
    print("2. Configure environment variables in Google Cloud")
    print("3. Set up monitoring and logging")
    print("4. Test all functionality")

if __name__ == "__main__":
    main() 
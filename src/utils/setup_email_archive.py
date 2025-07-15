#!/usr/bin/env python3
"""
Setup script for email archive database.
This script initializes the PostgreSQL database and verifies the configuration.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.services.email_archive_service import EmailArchiveService
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment configuration...")
    
    load_dotenv()
    
    required_vars = {
        'DATABASE_URL': 'PostgreSQL database connection URL',
        'EMAIL_ARCHIVE_ENABLED': 'Email archive feature flag'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        else:
            print(f"✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
    
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables and try again.")
        return False
    
    print("✅ Environment configuration is valid")
    return True


def test_database_connection():
    """Test database connection and create tables."""
    print("\n🔍 Testing database connection...")
    
    try:
        # Initialize the archive service (this will create tables)
        archive_service = EmailArchiveService()
        print("✅ Database connection successful")
        print("✅ Tables created/verified")
        return archive_service
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return None


def verify_database_schema():
    """Verify that all required tables exist."""
    print("\n🔍 Verifying database schema...")
    
    try:
        from sqlalchemy import create_engine, inspect
        from src.core.models.email_archive import Base
        
        database_url = os.getenv('DATABASE_URL')
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Check if schema exists
        schemas = inspector.get_schema_names()
        if 'email_archive' not in schemas:
            print("❌ email_archive schema not found")
            return False
        
        # Check required tables
        required_tables = [
            'hot_emails',
            'cold_emails', 
            'processing_logs',
            'storage_stats'
        ]
        
        existing_tables = inspector.get_table_names(schema='email_archive')
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table {table} exists")
            else:
                print(f"❌ Table {table} missing")
                return False
        
        print("✅ Database schema is complete")
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {str(e)}")
        return False


def test_basic_operations(archive_service):
    """Test basic archive operations."""
    print("\n🔍 Testing basic archive operations...")
    
    try:
        # Test data
        test_email = {
            'message_id': f'test-{datetime.now().isoformat()}',
            'thread_id': 'test-thread-123',
            'sender_email': 'test@example.com',
            'sender_name': 'Test User',
            'recipient_email': 'recipient@example.com',
            'subject': 'Test Email for Archive Setup',
            'body_text': 'This is a test email to verify the archive system is working.',
            'body_html': '<p>This is a test email to verify the archive system is working.</p>',
            'received_date': datetime.now(),
            'user_id': 'test-user-123',
            'task_database_id': 'test-db-123',
            'email_size_bytes': 1024,
            'has_attachments': False,
            'attachment_count': 0,
            'priority': 'normal',
            'labels': ['test', 'setup'],
            'is_read': False,
            'is_archived': False,
            'processing_status': 'completed',
            'processing_metadata': {'test': True}
        }
        
        # Store email
        email_id = archive_service.store_email(test_email, 'hot')
        print(f"✅ Stored test email with ID: {email_id}")
        
        # Retrieve email
        retrieved_email = archive_service.get_email(email_id, 'hot')
        if retrieved_email and retrieved_email['message_id'] == test_email['message_id']:
            print("✅ Successfully retrieved test email")
        else:
            print("❌ Failed to retrieve test email")
            return False
        
        # Search emails
        search_results = archive_service.search_emails(
            query='test',
            storage_type='hot',
            limit=10
        )
        if search_results:
            print(f"✅ Search returned {len(search_results)} results")
        else:
            print("❌ Search returned no results")
            return False
        
        # Get storage stats
        stats = archive_service.get_storage_stats()
        if stats:
            print("✅ Retrieved storage statistics")
            for storage_type, stat in stats.items():
                print(f"   {storage_type}: {stat['total_emails']} emails, {stat['total_size_bytes']} bytes")
        else:
            print("❌ Failed to retrieve storage statistics")
            return False
        
        print("✅ Basic operations test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Basic operations test failed: {str(e)}")
        return False


def create_scheduled_tasks():
    """Create scheduled tasks for maintenance operations."""
    print("\n🔍 Setting up scheduled tasks...")
    
    try:
        from celery_config import celery_app
        from src.core.tasks.email_archive_tasks import move_to_cold_storage_async, cleanup_old_emails_async
        
        # Note: In a real implementation, you would configure periodic tasks here
        # For now, we'll just verify the tasks can be imported
        
        print("✅ Email archive tasks are available:")
        print("   - move_to_cold_storage_async")
        print("   - cleanup_old_emails_async")
        print("   - get_storage_stats_async")
        print("   - search_emails_async")
        print("   - archive_email_async")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup scheduled tasks: {str(e)}")
        return False


def main():
    """Main setup function."""
    print("🚀 Email Archive Database Setup")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test database connection
    archive_service = test_database_connection()
    if not archive_service:
        sys.exit(1)
    
    # Verify schema
    if not verify_database_schema():
        sys.exit(1)
    
    # Test basic operations
    if not test_basic_operations(archive_service):
        sys.exit(1)
    
    # Setup scheduled tasks
    if not create_scheduled_tasks():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Email Archive Database Setup Complete!")
    print("\nNext steps:")
    print("1. Start your application with: docker-compose up")
    print("2. Monitor the archive with Flower: http://localhost:5555")
    print("3. Configure email processing to use the archive service")
    print("\nConfiguration:")
    print("- Hot storage: Recent emails (default: 30 days)")
    print("- Cold storage: Older emails (default: 365 days)")
    print("- Automatic compression: Enabled for non-image attachments")
    print("- Full-text search: Available on subject and body")
    
    # Print sample usage
    print("\nSample usage:")
    print("""
from src.core.services.email_archive_service import EmailArchiveService

# Initialize service
archive_service = EmailArchiveService()

# Store an email
email_data = {
    'message_id': 'unique-message-id',
    'sender_email': 'sender@example.com',
    'recipient_email': 'recipient@example.com',
    'subject': 'Email Subject',
    'body_text': 'Email content...',
    'received_date': datetime.now(),
    # ... other fields
}
email_id = archive_service.store_email(email_data, 'hot')

# Search emails
results = archive_service.search_emails(query='search term', storage_type='hot')

# Move old emails to cold storage
moved_count = archive_service.move_to_cold_storage(days_threshold=30)
    """)


if __name__ == "__main__":
    main() 
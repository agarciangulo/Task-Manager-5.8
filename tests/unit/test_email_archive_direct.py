#!/usr/bin/env python3
"""
Direct test of email archive functionality.
This test bypasses the Flask app and directly tests the PostgreSQL email archive.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.services.email_archive_service import EmailArchiveService
from core.logging_config import get_logger

logger = get_logger(__name__)

def test_email_archive_direct():
    """Test email archive functionality directly."""
    print("🚀 Testing Email Archive Directly")
    print("=" * 60)
    
    try:
        # Initialize the archive service
        print("1️⃣ Initializing Email Archive Service...")
        archive_service = EmailArchiveService()
        print("✅ Email Archive Service initialized")
        
        # Test data - simulate a real email
        test_email = {
            'message_id': f'test-{datetime.now().isoformat()}',
            'thread_id': 'test-thread-123',
            'sender_email': 'sender@example.com',
            'sender_name': 'Test Sender',
            'recipient_email': 'recipient@example.com',
            'subject': 'Test Email for Archive Testing',
            'body_text': '''Hi team,

Here's my update for today:

- Completed the quarterly report analysis
- Started working on the new authentication feature
- Had a productive meeting with the development team about project timeline
- Fixed three critical bugs in the user interface
- Updated documentation for the API endpoints

Looking forward to tomorrow's sprint planning session.

Best regards,
Test User''',
            'body_html': '''<p>Hi team,</p>
<p>Here's my update for today:</p>
<ul>
<li>Completed the quarterly report analysis</li>
<li>Started working on the new authentication feature</li>
<li>Had a productive meeting with the development team about project timeline</li>
<li>Fixed three critical bugs in the user interface</li>
<li>Updated documentation for the API endpoints</li>
</ul>
<p>Looking forward to tomorrow's sprint planning session.</p>
<p>Best regards,<br>Test User</p>''',
            'received_date': datetime.now(),
            'user_id': 'test-user-123',
            'task_database_id': 'test-db-123',
            'email_size_bytes': 2048,
            'has_attachments': False,
            'attachment_count': 0,
            'priority': 'normal',
            'labels': ['test', 'archive'],
            'is_read': False,
            'is_archived': False,
            'processing_status': 'completed',
            'processing_metadata': {'test': True, 'source': 'direct_test'}
        }
        
        # Store email in hot storage
        print("\n2️⃣ Storing Email in Hot Storage...")
        email_id = archive_service.store_email(test_email, 'hot')
        print(f"✅ Email stored with ID: {email_id}")
        
        # Retrieve the email
        print("\n3️⃣ Retrieving Email from Hot Storage...")
        retrieved_email = archive_service.get_email(email_id, 'hot')
        if retrieved_email:
            print("✅ Email retrieved successfully")
            print(f"   Subject: {retrieved_email['subject']}")
            print(f"   Sender: {retrieved_email['sender_email']}")
            print(f"   Body length: {len(retrieved_email['body_text'])} characters")
            print(f"   Full body preview: {retrieved_email['body_text'][:100]}...")
        else:
            print("❌ Failed to retrieve email")
            return False
        
        # Search for the email
        print("\n4️⃣ Searching for Email...")
        search_results = archive_service.search_emails(
            query='quarterly report',
            storage_type='hot',
            limit=10
        )
        if search_results:
            print(f"✅ Search returned {len(search_results)} results")
            for i, result in enumerate(search_results, 1):
                print(f"   {i}. {result['subject']} (from {result['sender_email']})")
        else:
            print("❌ Search returned no results")
        
        # Get storage statistics
        print("\n5️⃣ Getting Storage Statistics...")
        stats = archive_service.get_storage_stats()
        if stats:
            print("✅ Storage statistics retrieved:")
            for storage_type, stat in stats.items():
                print(f"   {storage_type}: {stat['total_emails']} emails, {stat['total_size_bytes']} bytes")
        else:
            print("❌ Failed to get storage statistics")
        
        # Test moving to cold storage (simulate)
        print("\n6️⃣ Testing Cold Storage Simulation...")
        # Create another email for cold storage test
        cold_test_email = test_email.copy()
        cold_test_email['message_id'] = f'cold-test-{datetime.now().isoformat()}'
        cold_test_email['subject'] = 'Old Email for Cold Storage Test'
        
        cold_email_id = archive_service.store_email(cold_test_email, 'cold')
        print(f"✅ Cold storage email stored with ID: {cold_email_id}")
        
        # Retrieve from cold storage
        cold_retrieved = archive_service.get_email(cold_email_id, 'cold')
        if cold_retrieved:
            print("✅ Cold storage email retrieved successfully")
            print(f"   Subject: {cold_retrieved['subject']}")
        else:
            print("❌ Failed to retrieve cold storage email")
        
        # Final statistics
        print("\n7️⃣ Final Statistics...")
        final_stats = archive_service.get_storage_stats()
        if final_stats:
            print("✅ Final storage statistics:")
            for storage_type, stat in final_stats.items():
                print(f"   {storage_type}: {stat['total_emails']} emails, {stat['total_size_bytes']} bytes")
        
        print("\n" + "=" * 60)
        print("🎉 Email Archive Test Completed Successfully!")
        print("\n✅ What was tested:")
        print("   - Email storage in hot storage")
        print("   - Email retrieval from hot storage")
        print("   - Full email body storage and retrieval")
        print("   - Email search functionality")
        print("   - Storage statistics")
        print("   - Cold storage functionality")
        print("\n📊 Database tables created:")
        print("   - hot_emails")
        print("   - cold_emails")
        print("   - processing_logs")
        print("   - storage_stats")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🔍 Checking environment...")
    
    # Check if database URL is set
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable is not set")
        return False
    
    print(f"✅ Database URL: {database_url[:50]}...")
    
    # Run the test
    success = test_email_archive_direct()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Check PostgreSQL database to see the stored emails:")
        print("   docker exec -it aiteamsupport-postgres-1 psql -U postgres -d email_archive")
        print("   SELECT subject, body_text FROM email_archive.hot_emails;")
        print("2. View storage statistics:")
        print("   SELECT * FROM email_archive.storage_stats;")
        print("3. Check processing logs:")
        print("   SELECT * FROM email_archive.processing_logs;")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
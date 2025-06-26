#!/usr/bin/env python3
"""
Migration script to add hybrid storage columns to email archive tables.
This script adds body_preview, body_storage_key, and has_full_body columns
and migrates existing data to the new hybrid storage approach.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import text

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.services.email_archive_service import EmailArchiveService
from core.logging_config import get_logger

logger = get_logger(__name__)


def migrate_email_storage():
    """Migrate existing email storage to hybrid approach."""
    print("🔄 Starting email storage migration...")
    
    try:
        # Initialize archive service
        archive_service = EmailArchiveService()
        
        # Get database session
        session = archive_service._get_session()
        
        # Add new columns to hot_emails table
        print("📝 Adding new columns to hot_emails table...")
        session.execute(text("""
            ALTER TABLE email_archive.hot_emails 
            ADD COLUMN IF NOT EXISTS body_preview TEXT,
            ADD COLUMN IF NOT EXISTS body_storage_key VARCHAR(255),
            ADD COLUMN IF NOT EXISTS has_full_body BOOLEAN DEFAULT FALSE;
        """))
        
        # Add new columns to cold_emails table
        print("📝 Adding new columns to cold_emails table...")
        session.execute(text("""
            ALTER TABLE email_archive.cold_emails 
            ADD COLUMN IF NOT EXISTS body_preview TEXT,
            ADD COLUMN IF NOT EXISTS body_storage_key VARCHAR(255),
            ADD COLUMN IF NOT EXISTS has_full_body BOOLEAN DEFAULT FALSE;
        """))
        
        session.commit()
        print("✅ New columns added successfully")
        
        # Migrate existing data
        print("🔄 Migrating existing email data...")
        
        # Process hot emails
        hot_emails = session.execute(text("""
            SELECT id, body_text FROM email_archive.hot_emails 
            WHERE body_preview IS NULL AND body_text IS NOT NULL
        """)).fetchall()
        
        migrated_count = 0
        for email_id, body_text in hot_emails:
            if body_text:
                # Create preview
                preview_length = 250
                if len(body_text) > preview_length:
                    body_preview = body_text[:preview_length] + "..."
                    has_full_body = True
                    
                    # Store full body in file
                    storage_key = archive_service._store_full_email_body(str(email_id), body_text)
                else:
                    body_preview = body_text
                    has_full_body = False
                    storage_key = None
                
                # Update database record
                session.execute(text("""
                    UPDATE email_archive.hot_emails 
                    SET body_preview = :body_preview, body_storage_key = :storage_key, has_full_body = :has_full_body
                    WHERE id = :email_id
                """), {
                    'body_preview': body_preview,
                    'storage_key': storage_key,
                    'has_full_body': has_full_body,
                    'email_id': email_id
                })
                
                migrated_count += 1
        
        # Process cold emails
        cold_emails = session.execute(text("""
            SELECT id, body_text FROM email_archive.cold_emails 
            WHERE body_preview IS NULL AND body_text IS NOT NULL
        """)).fetchall()
        
        for email_id, body_text in cold_emails:
            if body_text:
                # Create preview
                preview_length = 250
                if len(body_text) > preview_length:
                    body_preview = body_text[:preview_length] + "..."
                    has_full_body = True
                    
                    # Store full body in file
                    storage_key = archive_service._store_full_email_body(str(email_id), body_text)
                else:
                    body_preview = body_text
                    has_full_body = False
                    storage_key = None
                
                # Update database record
                session.execute(text("""
                    UPDATE email_archive.cold_emails 
                    SET body_preview = :body_preview, body_storage_key = :storage_key, has_full_body = :has_full_body
                    WHERE id = :email_id
                """), {
                    'body_preview': body_preview,
                    'storage_key': storage_key,
                    'has_full_body': has_full_body,
                    'email_id': email_id
                })
                
                migrated_count += 1
        
        session.commit()
        print(f"✅ Migrated {migrated_count} emails to hybrid storage")
        
        # Create indexes for better performance
        print("📊 Creating indexes for new columns...")
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_hot_emails_body_preview ON email_archive.hot_emails USING gin(to_tsvector('english', body_preview));"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_cold_emails_body_preview ON email_archive.cold_emails USING gin(to_tsvector('english', body_preview));"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_hot_emails_has_full_body ON email_archive.hot_emails(has_full_body);"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_cold_emails_has_full_body ON email_archive.cold_emails(has_full_body);"))
        
        session.commit()
        print("✅ Indexes created successfully")
        
        # Show migration summary
        hot_count = session.execute(text("SELECT COUNT(*) FROM email_archive.hot_emails")).scalar()
        cold_count = session.execute(text("SELECT COUNT(*) FROM email_archive.cold_emails")).scalar()
        full_body_count = session.execute(text("SELECT COUNT(*) FROM email_archive.hot_emails WHERE has_full_body = true")).scalar()
        
        print("\n📊 Migration Summary:")
        print(f"   Hot emails: {hot_count}")
        print(f"   Cold emails: {cold_count}")
        print(f"   Emails with full body in files: {full_body_count}")
        print(f"   Storage directory: {archive_service.storage_path}")
        
        session.close()
        print("\n🎉 Email storage migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        logger.error(f"Migration failed: {str(e)}")
        return False


if __name__ == "__main__":
    load_dotenv()
    success = migrate_email_storage()
    sys.exit(0 if success else 1) 
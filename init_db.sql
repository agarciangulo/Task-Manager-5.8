-- Initialize Email Archive Database
-- This script sets up the database schema for hot and cold storage email archiving

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For GIN indexes

-- Create schema for email archiving
CREATE SCHEMA IF NOT EXISTS email_archive;

-- Hot Storage Table (recent emails, frequently accessed)
CREATE TABLE IF NOT EXISTS email_archive.hot_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255),
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT,
    body_text TEXT,
    body_html TEXT,
    received_date TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(255),  -- Link to your user system
    task_database_id VARCHAR(255),  -- Link to Notion task database
    email_size_bytes INTEGER,
    has_attachments BOOLEAN DEFAULT FALSE,
    attachment_count INTEGER DEFAULT 0,
    priority VARCHAR(20) DEFAULT 'normal',
    labels TEXT[],  -- Array of Gmail labels
    is_read BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cold Storage Table (older emails, less frequently accessed)
CREATE TABLE IF NOT EXISTS email_archive.cold_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255),
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT,
    body_text TEXT,
    body_html TEXT,
    received_date TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(255),
    task_database_id VARCHAR(255),
    email_size_bytes INTEGER,
    has_attachments BOOLEAN DEFAULT FALSE,
    attachment_count INTEGER DEFAULT 0,
    priority VARCHAR(20) DEFAULT 'normal',
    labels TEXT[],
    is_read BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_metadata JSONB,
    archived_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email Attachments Table
CREATE TABLE IF NOT EXISTS email_archive.email_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL,
    storage_type VARCHAR(20) NOT NULL CHECK (storage_type IN ('hot', 'cold')),
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size_bytes INTEGER,
    file_path TEXT,  -- Path to stored file
    file_hash VARCHAR(64),  -- SHA-256 hash for deduplication
    is_compressed BOOLEAN DEFAULT FALSE,
    compression_ratio DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email Processing Log Table
CREATE TABLE IF NOT EXISTS email_archive.processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL,
    storage_type VARCHAR(20) NOT NULL CHECK (storage_type IN ('hot', 'cold')),
    processing_step VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    processing_time_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Storage Statistics Table
CREATE TABLE IF NOT EXISTS email_archive.storage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    storage_type VARCHAR(20) NOT NULL CHECK (storage_type IN ('hot', 'cold')),
    total_emails INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    total_attachments INTEGER DEFAULT 0,
    oldest_email_date TIMESTAMP WITH TIME ZONE,
    newest_email_date TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
-- Hot storage indexes
CREATE INDEX IF NOT EXISTS idx_hot_emails_user_id ON email_archive.hot_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_hot_emails_received_date ON email_archive.hot_emails(received_date);
CREATE INDEX IF NOT EXISTS idx_hot_emails_sender_email ON email_archive.hot_emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_hot_emails_thread_id ON email_archive.hot_emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_hot_emails_processing_status ON email_archive.hot_emails(processing_status);
CREATE INDEX IF NOT EXISTS idx_hot_emails_subject_gin ON email_archive.hot_emails USING gin(to_tsvector('english', subject));
CREATE INDEX IF NOT EXISTS idx_hot_emails_body_text_gin ON email_archive.hot_emails USING gin(to_tsvector('english', body_text));

-- Cold storage indexes
CREATE INDEX IF NOT EXISTS idx_cold_emails_user_id ON email_archive.cold_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_cold_emails_received_date ON email_archive.cold_emails(received_date);
CREATE INDEX IF NOT EXISTS idx_cold_emails_sender_email ON email_archive.cold_emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_cold_emails_thread_id ON email_archive.cold_emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_cold_emails_archived_date ON email_archive.cold_emails(archived_date);
CREATE INDEX IF NOT EXISTS idx_cold_emails_subject_gin ON email_archive.cold_emails USING gin(to_tsvector('english', subject));
CREATE INDEX IF NOT EXISTS idx_cold_emails_body_text_gin ON email_archive.cold_emails USING gin(to_tsvector('english', body_text));

-- Attachment indexes
CREATE INDEX IF NOT EXISTS idx_attachments_email_id ON email_archive.email_attachments(email_id);
CREATE INDEX IF NOT EXISTS idx_attachments_storage_type ON email_archive.email_attachments(storage_type);
CREATE INDEX IF NOT EXISTS idx_attachments_file_hash ON email_archive.email_attachments(file_hash);

-- Processing log indexes
CREATE INDEX IF NOT EXISTS idx_processing_logs_email_id ON email_archive.processing_logs(email_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_created_at ON email_archive.processing_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_processing_logs_status ON email_archive.processing_logs(status);

-- Create foreign key constraints
ALTER TABLE email_archive.email_attachments 
ADD CONSTRAINT fk_attachments_hot_email 
FOREIGN KEY (email_id) REFERENCES email_archive.hot_emails(id) ON DELETE CASCADE;

ALTER TABLE email_archive.email_attachments 
ADD CONSTRAINT fk_attachments_cold_email 
FOREIGN KEY (email_id) REFERENCES email_archive.cold_emails(id) ON DELETE CASCADE;

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_hot_emails_updated_at 
    BEFORE UPDATE ON email_archive.hot_emails 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cold_emails_updated_at 
    BEFORE UPDATE ON email_archive.cold_emails 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initialize storage statistics
INSERT INTO email_archive.storage_stats (storage_type, total_emails, total_size_bytes, total_attachments)
VALUES 
    ('hot', 0, 0, 0),
    ('cold', 0, 0, 0)
ON CONFLICT DO NOTHING;

-- Create a function to move emails from hot to cold storage
CREATE OR REPLACE FUNCTION email_archive.move_to_cold_storage(
    days_threshold INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    moved_count INTEGER := 0;
    email_record RECORD;
BEGIN
    -- Move emails older than the threshold from hot to cold storage
    FOR email_record IN 
        SELECT * FROM email_archive.hot_emails 
        WHERE received_date < NOW() - INTERVAL '1 day' * days_threshold
    LOOP
        -- Insert into cold storage
        INSERT INTO email_archive.cold_emails (
            message_id, thread_id, sender_email, sender_name, recipient_email,
            subject, body_text, body_html, received_date, processed_date,
            user_id, task_database_id, email_size_bytes, has_attachments,
            attachment_count, priority, labels, is_read, is_archived,
            processing_status, processing_metadata
        ) VALUES (
            email_record.message_id, email_record.thread_id, email_record.sender_email,
            email_record.sender_name, email_record.recipient_email, email_record.subject,
            email_record.body_text, email_record.body_html, email_record.received_date,
            email_record.processed_date, email_record.user_id, email_record.task_database_id,
            email_record.email_size_bytes, email_record.has_attachments, email_record.attachment_count,
            email_record.priority, email_record.labels, email_record.is_read, email_record.is_archived,
            email_record.processing_status, email_record.processing_metadata
        );
        
        -- Move attachments
        UPDATE email_archive.email_attachments 
        SET storage_type = 'cold' 
        WHERE email_id = email_record.id;
        
        -- Delete from hot storage
        DELETE FROM email_archive.hot_emails WHERE id = email_record.id;
        
        moved_count := moved_count + 1;
    END LOOP;
    
    RETURN moved_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA email_archive TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA email_archive TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA email_archive TO postgres; 
-- Migration: Polymorphic association for email_attachments
-- Date: 2024-06-25

-- 1. Rename column storage_type to email_type
ALTER TABLE email_archive.email_attachments
    RENAME COLUMN storage_type TO email_type;

-- 2. Drop old constraint and add new constraint for email_type
ALTER TABLE email_archive.email_attachments
    DROP CONSTRAINT IF EXISTS valid_storage_type;
ALTER TABLE email_archive.email_attachments
    ADD CONSTRAINT valid_email_type CHECK (email_type IN ('hot', 'cold'));

-- 3. Update indexes (if any were on storage_type)
DROP INDEX IF EXISTS idx_attachments_storage_type;
CREATE INDEX IF NOT EXISTS idx_attachments_email_type ON email_archive.email_attachments(email_type);

-- 4. (Optional) Update any data if needed (not required if only the column name changes)

-- 5. (Optional) Update foreign key constraints if you had any (not present in this model)

-- 6. (Optional) Update any application logic or triggers if they reference storage_type

-- End of migration 
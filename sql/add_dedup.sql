-- Add duplicate tracking column to obituaries table.
-- duplicate_of = NULL means this is the primary/canonical record.
-- duplicate_of = <id> means this row is a duplicate of that primary record.

ALTER TABLE obituaries
    ADD COLUMN duplicate_of INT DEFAULT NULL AFTER sent_to_cms;

CREATE INDEX idx_duplicate_of ON obituaries (duplicate_of);

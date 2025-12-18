-- Add subtitle field to books table
ALTER TABLE books ADD COLUMN IF NOT EXISTS subtitle TEXT;

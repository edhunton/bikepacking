-- Add amazon_link field to books table for direct Amazon product URLs
ALTER TABLE books ADD COLUMN IF NOT EXISTS amazon_link TEXT;

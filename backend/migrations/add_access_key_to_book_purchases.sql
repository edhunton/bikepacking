-- Add access_key column to book_purchases table
ALTER TABLE book_purchases ADD COLUMN IF NOT EXISTS access_key TEXT UNIQUE;

-- Create index for faster lookups by access key
CREATE INDEX IF NOT EXISTS idx_book_purchases_access_key ON book_purchases(access_key);

-- Generate access keys for existing purchases (optional - run if you have existing data)
-- UPDATE book_purchases SET access_key = encode(gen_random_bytes(32), 'base64') WHERE access_key IS NULL;

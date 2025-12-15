-- Add purchase_url to books for external sales links
ALTER TABLE books ADD COLUMN IF NOT EXISTS purchase_url TEXT;

-- Optional index if you query/filter by purchase_url (not required for simple reads)
-- CREATE INDEX IF NOT EXISTS idx_books_purchase_url ON books(purchase_url);

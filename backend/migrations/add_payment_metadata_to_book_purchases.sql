-- Add payment tracking fields to book_purchases table
ALTER TABLE book_purchases ADD COLUMN IF NOT EXISTS payment_id TEXT;
ALTER TABLE book_purchases ADD COLUMN IF NOT EXISTS payment_provider TEXT DEFAULT 'square';
ALTER TABLE book_purchases ADD COLUMN IF NOT EXISTS payment_amount INTEGER; -- Amount in smallest currency unit (e.g., cents)
ALTER TABLE book_purchases ADD COLUMN IF NOT EXISTS payment_currency TEXT DEFAULT 'GBP';

-- Create index on payment_id for faster lookups and idempotency checks
CREATE INDEX IF NOT EXISTS idx_book_purchases_payment_id ON book_purchases(payment_id);

-- Add comment
COMMENT ON COLUMN book_purchases.payment_id IS 'Payment ID from payment provider (e.g., Square payment ID) for idempotency';
COMMENT ON COLUMN book_purchases.payment_provider IS 'Payment provider name (e.g., square, stripe, manual)';
COMMENT ON COLUMN book_purchases.payment_amount IS 'Payment amount in smallest currency unit (e.g., cents for USD/GBP)';
COMMENT ON COLUMN book_purchases.payment_currency IS 'Payment currency code (e.g., GBP, USD)';



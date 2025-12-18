-- Create book_purchases table to track which users have purchased which books
CREATE TABLE IF NOT EXISTS book_purchases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, book_id) -- Prevent duplicate purchases
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_book_purchases_user_id ON book_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_book_purchases_book_id ON book_purchases(book_id);
CREATE INDEX IF NOT EXISTS idx_book_purchases_user_book ON book_purchases(user_id, book_id);

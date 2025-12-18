-- Create book_photos table to store images per book
CREATE TABLE IF NOT EXISTS book_photos (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    thumbnail_url TEXT,
    caption TEXT,
    taken_at TIMESTAMP NULL,
    latitude DOUBLE PRECISION NULL,
    longitude DOUBLE PRECISION NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_book_photos_book_id ON book_photos(book_id);
CREATE INDEX IF NOT EXISTS idx_book_photos_created_at ON book_photos(created_at);



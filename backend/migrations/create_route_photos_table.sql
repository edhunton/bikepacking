-- Create route_photos table for storing photos associated with routes
CREATE TABLE IF NOT EXISTS route_photos (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    thumbnail_url TEXT,
    caption TEXT,
    taken_at TIMESTAMP,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on route_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_route_photos_route_id ON route_photos(route_id);

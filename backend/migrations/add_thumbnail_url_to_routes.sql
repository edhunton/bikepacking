-- Add thumbnail_url field to routes table
ALTER TABLE routes ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_routes_thumbnail_url ON routes(thumbnail_url) WHERE thumbnail_url IS NOT NULL;

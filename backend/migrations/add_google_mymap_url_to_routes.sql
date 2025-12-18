-- Add google_mymap_url field to routes table
ALTER TABLE routes ADD COLUMN IF NOT EXISTS google_mymap_url TEXT; -- Link to Google MyMap

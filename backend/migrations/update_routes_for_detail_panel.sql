-- Change time to min_time and max_time for route duration range
ALTER TABLE routes DROP COLUMN IF EXISTS time;
ALTER TABLE routes ADD COLUMN IF NOT EXISTS min_time DECIMAL(10, 2); -- Minimum time in days
ALTER TABLE routes ADD COLUMN IF NOT EXISTS max_time DECIMAL(10, 2); -- Maximum time in days

-- Add new fields for route detail panel
ALTER TABLE routes ADD COLUMN IF NOT EXISTS description TEXT; -- Detailed description
ALTER TABLE routes ADD COLUMN IF NOT EXISTS strava_activities TEXT; -- JSON array or comma-separated Strava activity IDs/URLs
ALTER TABLE routes ADD COLUMN IF NOT EXISTS google_mymap_url TEXT; -- Link to Google MyMap
ALTER TABLE routes ADD COLUMN IF NOT EXISTS komoot_collections TEXT; -- JSON array or comma-separated Komoot collection IDs/URLs

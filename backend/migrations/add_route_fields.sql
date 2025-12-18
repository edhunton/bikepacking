-- Add new fields to routes table for improved route editing
ALTER TABLE routes ADD COLUMN IF NOT EXISTS time DECIMAL(10, 2); -- Time in days
ALTER TABLE routes ADD COLUMN IF NOT EXISTS off_road_distance DECIMAL(10, 2); -- Off-road distance in kilometers
ALTER TABLE routes ADD COLUMN IF NOT EXISTS off_road_percentage DECIMAL(5, 2); -- Percentage of route that is off-road (0-100)
ALTER TABLE routes ADD COLUMN IF NOT EXISTS grade VARCHAR(50); -- Grade: easy, moderate, difficult, hard

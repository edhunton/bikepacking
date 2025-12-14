-- Add live field to routes table for soft delete functionality
ALTER TABLE routes ADD COLUMN IF NOT EXISTS live BOOLEAN DEFAULT TRUE;

-- Create index on live field for faster filtering
CREATE INDEX IF NOT EXISTS idx_routes_live ON routes(live);

-- Update any existing routes to be live by default
UPDATE routes SET live = TRUE WHERE live IS NULL;

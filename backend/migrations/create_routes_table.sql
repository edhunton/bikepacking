-- Create routes table
CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    gpx_url TEXT,
    difficulty VARCHAR(50),
    country VARCHAR(100),
    county VARCHAR(100),
    distance DECIMAL(10, 2), -- in kilometers
    ascent INTEGER, -- in meters (elevation gain)
    descent INTEGER, -- in meters (elevation loss)
    starting_station VARCHAR(255),
    ending_station VARCHAR(255),
    getting_there TEXT,
    bike_choice TEXT,
    guidebook_id INTEGER REFERENCES books(id) ON DELETE SET NULL, -- Foreign key to books table, nullable for routes not in guidebooks
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on guidebook_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_routes_guidebook_id ON routes(guidebook_id);

-- Create index on country and county for filtering
CREATE INDEX IF NOT EXISTS idx_routes_country ON routes(country);
CREATE INDEX IF NOT EXISTS idx_routes_county ON routes(county);

-- Create index on difficulty for filtering
CREATE INDEX IF NOT EXISTS idx_routes_difficulty ON routes(difficulty);

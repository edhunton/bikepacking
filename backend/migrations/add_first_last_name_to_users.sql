-- Add first_name and last_name columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255);

-- Migrate existing data: split name into first_name and last_name
-- This assumes existing names are in "First Last" format
UPDATE users 
SET 
  first_name = SPLIT_PART(name, ' ', 1),
  last_name = CASE 
    WHEN POSITION(' ' IN name) > 0 THEN SUBSTRING(name FROM POSITION(' ' IN name) + 1)
    ELSE ''
  END
WHERE first_name IS NULL AND name IS NOT NULL;

-- Make first_name and last_name NOT NULL after migration
-- Note: For new signups, we'll require both fields
-- ALTER TABLE users ALTER COLUMN first_name SET NOT NULL;
-- ALTER TABLE users ALTER COLUMN last_name SET NOT NULL;



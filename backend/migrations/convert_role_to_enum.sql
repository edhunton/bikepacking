-- Convert role column from VARCHAR to ENUM type
-- This migration creates a user_role enum and converts the existing role column
-- It's idempotent and safe to run multiple times

-- Step 1: Create the enum type if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('user', 'admin');
    END IF;
END $$;

-- Step 2: Check if we need to convert the column
DO $$
DECLARE
    col_type text;
BEGIN
    -- Get the current data type of the role column
    SELECT udt_name INTO col_type
    FROM information_schema.columns
    WHERE table_schema = 'public' 
      AND table_name = 'users' 
      AND column_name = 'role';
    
    -- Only convert if it's currently varchar/text
    IF col_type = 'varchar' OR col_type = 'text' OR col_type IS NULL THEN
        -- Ensure all existing role values are valid (convert any invalid values to 'user')
        UPDATE users 
        SET role = 'user' 
        WHERE role IS NOT NULL 
          AND role NOT IN ('user', 'admin');
        
        -- Add a temporary column with the enum type
        ALTER TABLE users ADD COLUMN IF NOT EXISTS role_temp user_role;
        
        -- Populate the temporary column with converted values (cast string to enum)
        UPDATE users 
        SET role_temp = CASE 
            WHEN role = 'admin' THEN 'admin'::user_role
            ELSE 'user'::user_role
        END
        WHERE role IS NOT NULL;
        
        -- Drop the old varchar column
        ALTER TABLE users DROP COLUMN IF EXISTS role;
        
        -- Rename the temporary column to role
        ALTER TABLE users RENAME COLUMN role_temp TO role;
        
        -- Set constraints
        ALTER TABLE users ALTER COLUMN role SET NOT NULL;
        ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user'::user_role;
        
        -- Recreate the index
        DROP INDEX IF EXISTS idx_users_role;
        CREATE INDEX idx_users_role ON users(role);
    ELSE
        -- Already an enum, just ensure values are valid and constraints are set
        UPDATE users 
        SET role = 'user'::user_role 
        WHERE role::text NOT IN ('user', 'admin');
        
        ALTER TABLE users ALTER COLUMN role SET NOT NULL;
        ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user'::user_role;
        
        -- Ensure index exists
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    END IF;
END $$;



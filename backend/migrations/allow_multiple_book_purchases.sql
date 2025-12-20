-- Allow users to buy multiple copies of the same book
-- Drop the unique constraint on (user_id, book_id)

-- Drop the unique constraint if it exists (try common constraint names)
ALTER TABLE book_purchases DROP CONSTRAINT IF EXISTS book_purchases_user_id_book_id_key;
ALTER TABLE book_purchases DROP CONSTRAINT IF EXISTS book_purchases_pkey;

-- Use a DO block to find and drop any unique constraint on (user_id, book_id)
DO $$ 
DECLARE
    constraint_name text;
BEGIN
    -- Find the constraint name for unique constraint on (user_id, book_id)
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'book_purchases'::regclass
    AND contype = 'u'
    AND array_length(conkey, 1) = 2
    AND (
        SELECT array_agg(attname ORDER BY attnum)
        FROM pg_attribute
        WHERE attrelid = conrelid
        AND attnum = ANY(conkey)
    ) = ARRAY['user_id', 'book_id']
    LIMIT 1;
    
    -- Drop the constraint if found
    IF constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE book_purchases DROP CONSTRAINT ' || quote_ident(constraint_name);
    END IF;
END $$;

-- Keep the indexes for performance (just remove the unique constraint)
-- The indexes on user_id and book_id are still useful for lookups


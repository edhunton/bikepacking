# Database Migrations

## Running the Routes Migration

To create the routes table in your database, run:

```bash
# Using psql directly
psql -h localhost -p 55432 -U postgres -d bikepacking -f migrations/create_routes_table.sql

# Or using docker exec if using docker-compose
docker exec -i bikepacking_postgres psql -U postgres -d bikepacking < migrations/create_routes_table.sql
```

## Seeding Routes Data

To populate the routes table with 10 dummy routes for frontend development:

**Option 1: With guidebook references** (requires books with IDs 1, 2, 3 to exist)
```bash
# Using psql directly
psql -h localhost -p 55432 -U postgres -d bikepacking -f migrations/seed_routes.sql

# Or using docker exec if using docker-compose
docker exec -i bikepacking_postgres psql -U postgres -d bikepacking < migrations/seed_routes.sql
```

**Option 2: Without guidebook references** (all routes standalone - use if you don't have books yet)
```bash
# Using psql directly
psql -h localhost -p 55432 -U postgres -d bikepacking -f migrations/seed_routes_no_guidebooks.sql

# Or using docker exec if using docker-compose
docker exec -i bikepacking_postgres psql -U postgres -d bikepacking < migrations/seed_routes_no_guidebooks.sql
```

**Note:** 
- `seed_routes.sql` includes 3 routes with guidebook_id references (1, 2, 3) and 7 standalone routes
- `seed_routes_no_guidebooks.sql` includes all 10 routes as standalone (no guidebook references)
- Use the second option if you don't have books in your database yet

## Migration Files

- `create_routes_table.sql` - Creates the routes table with all required fields and indexes
- `add_live_field_to_routes.sql` - Adds `live` boolean field for soft delete functionality (defaults to TRUE)
- `add_thumbnail_url_to_routes.sql` - Adds `thumbnail_url` field for storing route map thumbnails
- `add_purchase_url_to_books.sql` - Adds `purchase_url` field for external sales links per book
- `seed_routes.sql` - Seeds the routes table with 10 dummy routes (3 with guidebook references, 7 standalone)
- `seed_routes_no_guidebooks.sql` - Seeds the routes table with 10 dummy routes (all standalone, no guidebook references)

## Running the Live Field Migration

To add the soft delete functionality (live field):

```bash
# Using psql directly
psql -h localhost -p 55432 -U postgres -d bikepacking -f migrations/add_live_field_to_routes.sql

# Or using docker exec if using docker-compose
docker exec -i bikepacking_postgres psql -U postgres -d bikepacking < migrations/add_live_field_to_routes.sql
```

**Note:** After running this migration, deleted routes will have `live = FALSE` instead of being removed from the database. You can reinstate them by manually setting `live = TRUE` in the database.

## Running the Thumbnail URL Migration

To add the thumbnail URL field for route map thumbnails:

```bash
# Using psql directly
psql -h localhost -p 55432 -U postgres -d bikepacking -f migrations/add_thumbnail_url_to_routes.sql

# Or using docker exec if using docker-compose
docker exec -i bikepacking_postgres psql -U postgres -d bikepacking < migrations/add_thumbnail_url_to_routes.sql
```

**Note:** This migration adds a `thumbnail_url` field to store paths to generated Mapbox static image thumbnails. Thumbnails are automatically generated when routes are created/updated with GPX files, reducing Mapbox API calls.

## Running the Purchase URL Migration (Books)

To add the `purchase_url` field for storing external sales links:

```bash
# Using psql directly
psql -h localhost -p 55432 -U postgres -d bikepacking -f migrations/add_purchase_url_to_books.sql

# Or using docker exec if using docker-compose
docker exec -i bikepacking_postgres psql -U postgres -d bikepacking < migrations/add_purchase_url_to_books.sql
```

**Note:** Store links like Square checkout URLs here so each book carries its sales link.

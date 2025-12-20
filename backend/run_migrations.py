#!/usr/bin/env python3
"""Run database migrations for book_purchases table."""
import os
import sys
import psycopg
from pathlib import Path

def get_dsn():
    """Get database connection string from environment."""
    return os.getenv(
        "DATABASE_URL",
        "postgres://postgres:postgres@localhost:55432/bikepacking",
    )

def run_migration_file(conn, migration_file: Path):
    """Run a SQL migration file."""
    print(f"Running migration: {migration_file.name}")
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
        print(f"✓ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        print(f"✗ Error applying {migration_file.name}: {e}")
        conn.rollback()
        return False

def main():
    """Run all pending migrations."""
    migrations_dir = Path(__file__).parent / "migrations"
    
    # List of migration files in order
    migration_files = [
        migrations_dir / "add_access_key_to_book_purchases.sql",
        migrations_dir / "add_payment_metadata_to_book_purchases.sql",
    ]
    
    print("=" * 60)
    print("Running database migrations for book_purchases table")
    print("=" * 60)
    
    dsn = get_dsn()
    print(f"Connecting to database: {dsn.split('@')[1] if '@' in dsn else dsn}")
    
    try:
        with psycopg.connect(dsn) as conn:
            for migration_file in migration_files:
                if not migration_file.exists():
                    print(f"⚠ Migration file not found: {migration_file}")
                    continue
                
                if not run_migration_file(conn, migration_file):
                    print("\n✗ Migration failed. Stopping.")
                    sys.exit(1)
            
            print("\n" + "=" * 60)
            print("✓ All migrations completed successfully!")
            print("=" * 60)
    except Exception as e:
        print(f"\n✗ Failed to connect to database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


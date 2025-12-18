"""Functions for checking book purchase status and managing access keys."""
import os
import secrets
from contextlib import contextmanager
from typing import Generator, Optional
import psycopg


def _dsn() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgres://postgres:postgres@localhost:55432/bikepacking",
    )


@contextmanager
def get_connection():
    conn = psycopg.connect(_dsn())
    try:
        yield conn
    finally:
        conn.close()


def has_user_purchased_book(user_id: int, book_id: int) -> bool:
    """Check if a user has purchased a specific book."""
    query = """
        SELECT 1 FROM book_purchases
        WHERE user_id = %s AND book_id = %s
        LIMIT 1;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, book_id))
            return cur.fetchone() is not None


def get_user_purchased_books(user_id: int) -> list[int]:
    """Get a list of book IDs that a user has purchased."""
    query = """
        SELECT book_id FROM book_purchases
        WHERE user_id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            return [row[0] for row in cur.fetchall()]


def generate_access_key() -> str:
    """Generate a cryptographically secure random access key."""
    # Generate a 32-byte (256-bit) random key, base64-encoded for URL safety
    # This gives ~43 characters, URL-safe
    return secrets.token_urlsafe(32)


def create_purchase_with_key(user_id: int, book_id: int) -> str:
    """Create a purchase record and return the generated access key."""
    access_key = generate_access_key()
    query = """
        INSERT INTO book_purchases (user_id, book_id, access_key)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, book_id) DO UPDATE
        SET access_key = COALESCE(book_purchases.access_key, EXCLUDED.access_key)
        RETURNING access_key;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, book_id, access_key))
            result = cur.fetchone()
            conn.commit()
            return result[0] if result else access_key


def get_access_key(user_id: int, book_id: int) -> Optional[str]:
    """Get the access key for a user's purchase of a specific book."""
    query = """
        SELECT access_key FROM book_purchases
        WHERE user_id = %s AND book_id = %s
        LIMIT 1;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, book_id))
            result = cur.fetchone()
            return result[0] if result else None


def validate_access_key(access_key: str, book_id: int) -> Optional[int]:
    """
    Validate an access key for a specific book.
    Returns the user_id if valid, None otherwise.
    """
    query = """
        SELECT user_id FROM book_purchases
        WHERE access_key = %s AND book_id = %s
        LIMIT 1;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (access_key, book_id))
            result = cur.fetchone()
            return result[0] if result else None


def has_access_key(user_id: int, book_id: int) -> bool:
    """Check if a purchase has an access key."""
    query = """
        SELECT 1 FROM book_purchases
        WHERE user_id = %s AND book_id = %s AND access_key IS NOT NULL
        LIMIT 1;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, book_id))
            return cur.fetchone() is not None

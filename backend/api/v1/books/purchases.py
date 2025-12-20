"""Functions for checking book purchase status and managing access keys."""
import os
import secrets
import logging
from contextlib import contextmanager
from typing import Generator, Optional
import psycopg

logger = logging.getLogger(__name__)


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


def create_purchase_with_key(
    user_id: int, 
    book_id: int, 
    payment_id: Optional[str] = None,
    payment_provider: str = "manual",
    payment_amount: Optional[int] = None,
    payment_currency: str = "GBP"
) -> str:
    """
    Create a purchase record and return the generated access key.
    
    Args:
        user_id: User ID
        book_id: Book ID
        payment_id: Payment ID from payment provider (for idempotency)
        payment_provider: Payment provider name (e.g., 'square', 'stripe', 'manual')
        payment_amount: Payment amount in smallest currency unit
        payment_currency: Payment currency code
    """
    access_key = generate_access_key()
    
    # If payment_id is provided, check for existing purchase by payment_id first (idempotency)
    if payment_id:
        # Check if access_key column exists, if so use it, otherwise just check by payment_id
        check_query = """
            SELECT user_id, book_id FROM book_purchases
            WHERE payment_id = %s
            LIMIT 1;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(check_query, (payment_id,))
                    result = cur.fetchone()
                    if result:
                        # Purchase exists - get or generate access_key for this purchase
                        existing_user_id, existing_book_id = result
                        existing_key = get_access_key(existing_user_id, existing_book_id)
                        if existing_key:
                            return existing_key
                        # If no access_key exists, we'll generate one below and update the record
                except Exception as e:
                    # If query fails (e.g., payment_id column doesn't exist), continue to create purchase
                    logger.warning(f"Error checking existing purchase by payment_id: {e}")
    
    # Try to insert with all columns, but handle case where columns might not exist
    # Note: We allow multiple purchases of the same book, so no ON CONFLICT clause
    try:
        query = """
            INSERT INTO book_purchases (user_id, book_id, access_key, payment_id, payment_provider, payment_amount, payment_currency)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING access_key;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, book_id, access_key, payment_id, payment_provider, payment_amount, payment_currency))
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else access_key
    except Exception as e:
        # If columns don't exist, try without access_key and payment fields
        error_msg = str(e).lower()
        if "access_key" in error_msg or "payment_id" in error_msg or "column" in error_msg:
            logger.warning(f"Database columns may not exist, trying simplified insert: {e}")
            # Fallback: insert without access_key and payment fields
            # Allow multiple purchases, so no ON CONFLICT clause
            fallback_query = """
                INSERT INTO book_purchases (user_id, book_id)
                VALUES (%s, %s)
                RETURNING id;
            """
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(fallback_query, (user_id, book_id))
                    result = cur.fetchone()
                    conn.commit()
                    if result:
                        # Return a generated key anyway (even though not stored)
                        logger.info(f"Purchase created without access_key column. Generated key: {access_key}")
                        return access_key
                    else:
                        # Purchase already exists
                        logger.info("Purchase already exists")
                        return access_key
        else:
            # Re-raise if it's a different error
            raise


def get_access_key(user_id: int, book_id: int) -> Optional[str]:
    """Get the access key for a user's purchase of a specific book."""
    query = """
        SELECT access_key FROM book_purchases
        WHERE user_id = %s AND book_id = %s
        LIMIT 1;
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, book_id))
                result = cur.fetchone()
                return result[0] if result else None
    except Exception as e:
        # Column might not exist - return None
        error_msg = str(e).lower()
        if "access_key" in error_msg or "column" in error_msg:
            logger.warning(f"access_key column may not exist: {e}")
            return None
        raise


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



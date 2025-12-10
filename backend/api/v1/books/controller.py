from typing import List

from fastapi import HTTPException

from .db import get_connection
from .models import Book


def get_all_books() -> List[Book]:
    """
    Retrieve all books from the database.
    
    Returns:
        List of Book objects
        
    Raises:
        HTTPException: If database query fails
    """
    query = """
        SELECT id, title, author, published_at, isbn, cover_url
        FROM books
        ORDER BY id;
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        except Exception as exc:  # pragma: no cover - simple API surface
            raise HTTPException(status_code=500, detail="Error querying books") from exc

    return [
        Book(
            id=row[0],
            title=row[1],
            author=row[2],
            published_at=row[3],
            isbn=row[4] if len(row) > 4 else None,
            cover_url=row[5] if len(row) > 5 else None,
        )
        for row in rows
    ]

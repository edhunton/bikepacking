from typing import List

from fastapi import HTTPException

from .db import get_connection
from .models import Book, UpdateBook


def get_all_books() -> List[Book]:
    """
    Retrieve all books from the database.
    
    Returns:
        List of Book objects
        
    Raises:
        HTTPException: If database query fails
    """
    query = """
        SELECT id, title, author, published_at, isbn, cover_url, purchase_url
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
            purchase_url=row[6] if len(row) > 6 else None,
        )
        for row in rows
    ]


def get_book_by_id(book_id: int) -> Book:
    query = """
        SELECT id, title, author, published_at, isbn, cover_url, purchase_url
        FROM books
        WHERE id = %s;
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (book_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Book not found")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Error querying book") from exc

    return Book(
        id=row[0],
        title=row[1],
        author=row[2],
        published_at=row[3],
        isbn=row[4] if len(row) > 4 else None,
        cover_url=row[5] if len(row) > 5 else None,
        purchase_url=row[6] if len(row) > 6 else None,
    )


def update_book(book_id: int, data: UpdateBook) -> Book:
    existing = get_book_by_id(book_id)

    updates = []
    params = []
    if data.title is not None:
        updates.append("title = %s")
        params.append(data.title)
    if data.author is not None:
        updates.append("author = %s")
        params.append(data.author)
    if data.published_at is not None:
        updates.append("published_at = %s")
        params.append(data.published_at)
    if data.isbn is not None:
        updates.append("isbn = %s")
        params.append(data.isbn)
    if data.cover_url is not None:
        updates.append("cover_url = %s")
        params.append(data.cover_url)
    if data.purchase_url is not None:
        updates.append("purchase_url = %s")
        params.append(data.purchase_url)

    if not updates:
        return existing

    query = f"""
        UPDATE books
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, title, author, published_at, isbn, cover_url, purchase_url;
    """
    params.append(book_id)

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                conn.commit()
                if not row:
                    raise HTTPException(status_code=404, detail="Book not found")
        except HTTPException:
            raise
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=500, detail="Error updating book") from exc

    return Book(
        id=row[0],
        title=row[1],
        author=row[2],
        published_at=row[3],
        isbn=row[4],
        cover_url=row[5],
        purchase_url=row[6],
    )

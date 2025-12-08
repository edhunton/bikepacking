from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .db import get_connection

router = APIRouter()


class Book(BaseModel):
    id: int
    title: str
    author: str
    published_at: date | None = None
    isbn: str | None = None
    cover_url: str | None = None


@router.get("/health")
def health_check() -> dict[str, str]:
    # Lightweight endpoint to confirm the books router is live.
    return {"status": "ok"}


@router.get("/", response_model=List[Book])
def get_books() -> list[Book]:
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

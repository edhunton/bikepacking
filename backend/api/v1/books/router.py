from typing import List

from fastapi import APIRouter

from .controller import get_all_books, update_book
from .models import Book, UpdateBook

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    # Lightweight endpoint to confirm the books router is live.
    return {"status": "ok"}


@router.get("/", response_model=List[Book])
def get_books() -> list[Book]:
    """Get all books."""
    return get_all_books()


@router.put("/{book_id}", response_model=Book)
def update_book_endpoint(book_id: int, data: UpdateBook) -> Book:
    """Update a book by ID."""
    return update_book(book_id, data)

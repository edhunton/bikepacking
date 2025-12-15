from typing import List

from fastapi import APIRouter, UploadFile, File, Form

from .controller import (
    get_all_books,
    update_book,
    list_book_photos,
    save_book_photo,
    delete_book_photo,
)
from .models import Book, UpdateBook, BookPhoto, CreateBookPhoto

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


@router.get("/{book_id}/photos", response_model=list[BookPhoto])
def list_photos(book_id: int) -> list[BookPhoto]:
    """List photos for a book."""
    return list_book_photos(book_id)


@router.post("/photos", response_model=BookPhoto)
def upload_photo(
    book_id: int = Form(...),
    caption: str | None = Form(None),
    file: UploadFile = File(...),
) -> BookPhoto:
    """Upload a photo for a book."""
    return save_book_photo(file, book_id, caption)


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int):
    """Delete a book photo by ID."""
    return delete_book_photo(photo_id)

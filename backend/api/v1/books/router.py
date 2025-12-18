from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Depends

from .controller import (
    get_all_books,
    update_book,
    list_book_photos,
    save_book_photo,
    delete_book_photo,
)
from .models import Book, UpdateBook, BookPhoto, CreateBookPhoto
from .purchases import (
    has_user_purchased_book,
    get_access_key,
    create_purchase_with_key,
    validate_access_key,
)
from api.v1.users.controller import get_current_user
from api.v1.users.models import UserInDB

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


@router.get("/{book_id}/purchased")
def check_book_purchase(
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
) -> dict:
    """Check if the current user has purchased a specific book."""
    purchased = has_user_purchased_book(current_user.id, book_id)
    
    # Get or generate access key if purchased
    access_key = None
    if purchased:
        access_key = get_access_key(current_user.id, book_id)
        # If no key exists, generate one (this handles existing purchases)
        if not access_key:
            access_key = create_purchase_with_key(current_user.id, book_id)
    
    return {
        "purchased": purchased,
        "book_id": book_id,
        "access_key": access_key
    }


@router.get("/{book_id}/access-key")
def get_book_access_key(
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
) -> dict:
    """
    Get the unique access key for a purchased book.
    Creates a new key if the user has purchased but no key exists yet.
    """
    if not has_user_purchased_book(current_user.id, book_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="You must purchase this book to receive an access key"
        )
    
    access_key = get_access_key(current_user.id, book_id)
    if not access_key:
        # Generate key for existing purchase
        access_key = create_purchase_with_key(current_user.id, book_id)
    
    return {
        "book_id": book_id,
        "access_key": access_key,
        "message": "Keep this key private. It is tied to your account."
    }


@router.post("/{book_id}/validate-key")
def validate_book_access_key(
    book_id: int,
    access_key: str = Form(...)
) -> dict:
    """
    Validate an access key for a book.
    Returns user_id if valid, None otherwise.
    This endpoint does not require authentication.
    """
    user_id = validate_access_key(access_key, book_id)
    return {
        "valid": user_id is not None,
        "book_id": book_id,
        "user_id": user_id
    }

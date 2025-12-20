from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Depends

from .controller import (
    get_all_books,
    get_book_by_id,
    update_book,
    list_book_photos,
    save_book_photo,
    delete_book_photo,
)
from .payment_links import create_payment_link_for_user
from .models import Book, UpdateBook, BookPhoto, CreateBookPhoto
from .purchases import (
    has_user_purchased_book,
    get_access_key,
    create_purchase_with_key,
    validate_access_key,
)
from api.v1.users.controller import get_current_user
from api.v1.users.models import UserInDB
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

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


@router.get("/payment-links")
def get_payment_links_for_books(
    book_ids: str,  # Comma-separated list of book IDs (required)
    current_user: UserInDB = Depends(get_current_user)
) -> dict:
    """
    Get Square payment links for multiple books at once.
    
    This is more efficient than fetching links individually and allows
    pre-generating links when the page loads.
    
    Query params:
    - book_ids: Comma-separated list of book IDs (e.g., "1,2,3")
    """
    # Functions are already imported at the top of the file
    try:
        book_id_list = [int(bid.strip()) for bid in book_ids.split(",") if bid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid book_ids format. Use comma-separated integers.")
    
    payment_links = {}
    errors = {}
    
    for book_id in book_id_list:
        try:
            # Get book details (allow multiple purchases, so no check needed)
            book = get_book_by_id(book_id)
            
            # Create payment link
            price_cents = 999  # Default £9.99 - adjust as needed
            payment_link = create_payment_link_for_user(
                user_email=current_user.email,
                book_id=book_id,
                book_title=book.title,
                price_cents=price_cents,
                currency="GBP"
            )
            
            payment_links[book_id] = payment_link
            logger.info(f"Created payment link for book {book_id} ({book.title}): {payment_link}")
        except HTTPException as e:
            errors[book_id] = e.detail
        except Exception as e:
            errors[book_id] = str(e)
    
    return {
        "payment_links": payment_links,
        "errors": errors
    }


@router.get("/{book_id}/payment-link")
def get_payment_link(
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
) -> dict:
    """
    Get a Square payment link for purchasing this book.
    
    Creates a dynamic payment link with:
    - buyer_email: The logged-in user's email (for webhook user identification)
    - metadata.book_id: The book ID (for webhook book identification)
    
    The link is created on-demand and includes the user's email, so the webhook
    can automatically create the purchase record when payment completes.
    
    Note: Users can buy multiple copies, so no purchase check is performed.
    """
    # Get book details
    book = get_book_by_id(book_id)
    
    # Create dynamic payment link with user's email
    try:
        # Default price if not in book model (adjust based on your needs)
        # You may want to add price_cents to your Book model
        price_cents = 999  # Default £9.99 - adjust as needed
        
        payment_link = create_payment_link_for_user(
            user_email=current_user.email,
            book_id=book_id,
            book_title=book.title,
            price_cents=price_cents,
            currency="GBP"
        )
        
        return {
            "payment_link": payment_link,
            "book_id": book_id,
            "book_title": book.title
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions from create_payment_link_for_user
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create payment link: {str(e)}"
        )


@router.post("/{book_id}/purchase")
def create_manual_purchase(
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
) -> dict:
    """
    Manually create a purchase record for the current user.
    This is useful for:
    - Testing purchases
    - Manual admin grants
    - External purchase verification (e.g., Amazon)
    
    Note: For Square payments, purchases are automatically created via webhook.
    Users can buy multiple copies of the same book.
    """
    # Create new purchase (allow multiple purchases)
    try:
        access_key = create_purchase_with_key(
            user_id=current_user.id,
            book_id=book_id,
            payment_provider="manual"
        )
        return {
            "purchased": True,
            "book_id": book_id,
            "access_key": access_key,
            "message": "Purchase created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating purchase: {str(e)}")

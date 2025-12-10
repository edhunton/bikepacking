from typing import List

from fastapi import APIRouter

from .controller import get_all_books
from .models import Book

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    # Lightweight endpoint to confirm the books router is live.
    return {"status": "ok"}


@router.get("/", response_model=List[Book])
def get_books() -> list[Book]:
    """Get all books."""
    return get_all_books()

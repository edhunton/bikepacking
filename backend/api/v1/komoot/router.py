from typing import List, Optional

from fastapi import APIRouter, Query

from .controller import (
    get_tours as get_tours_controller,
    get_collections as get_collections_controller,
    clear_cache as clear_cache_controller,
)
from .models import KomootCollection, KomootTour

router = APIRouter()


@router.get("/tours", response_model=List[KomootTour])
def get_tours(
    per_page: int = Query(20, ge=1, le=100, description="Number of tours to return"),
    page: int = Query(1, ge=1, description="Page number"),
    tour_type: Optional[str] = Query(None, description="Filter by tour type (e.g., bike, hike)"),
    use_cache: bool = Query(True, description="Use cached results if available"),
) -> List[KomootTour]:
    """
    Fetch Komoot tours.
    
    Note: Komoot doesn't have an official public API. This endpoint uses
    unofficial methods that may require authentication.
    """
    tours = get_tours_controller(
        per_page=per_page,
        page=page,
        tour_type=tour_type,
        use_cache=use_cache,
    )
    return [KomootTour(**tour.to_dict()) for tour in tours]


@router.get("/collections", response_model=List[KomootCollection])
def get_collections(
    use_cache: bool = Query(True, description="Use cached results if available"),
) -> List[KomootCollection]:
    """
    Fetch Komoot collections.
    
    Collections are groups of tours, highlights, or routes that users organize.
    Note: This uses unofficial API methods and may require authentication.
    """
    return get_collections_controller(use_cache=use_cache)


@router.post("/cache/clear")
def clear_cache():
    """Clear the Komoot tours and collections cache."""
    return clear_cache_controller()

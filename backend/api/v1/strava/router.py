import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .controller import (
    get_activities as get_activities_controller,
    get_authorization_url,
    exchange_code_for_token,
    clear_activities_cache,
)
from .models import StravaActivity

router = APIRouter()

# Strava API credentials for authorization endpoint
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")


@router.get("/health")
def health_check() -> dict[str, str]:
    """Lightweight endpoint to confirm the Strava router is live."""
    return {"status": "ok"}


@router.post("/cache/clear")
def clear_cache() -> dict[str, str]:
    """Clear the activities cache. Useful for testing."""
    return clear_activities_cache()


@router.get("/authorize")
def get_authorize_url() -> dict[str, str]:
    """
    Get the Strava OAuth authorization URL.

    Visit this URL to authorize the app and get a new refresh token with proper scopes.
    After authorization, you'll receive a code that can be exchanged for tokens.
    """
    if not STRAVA_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="STRAVA_CLIENT_ID not configured. Please set it as an environment variable."
        )
    
    return {
        "authorization_url": get_authorization_url(),
        "instructions": (
            "1. Visit the authorization_url above\n"
            "2. Authorize the app\n"
            "3. Copy the 'code' parameter from the redirect URL\n"
            "4. Exchange the code for tokens using /api/v1/strava/token?code=YOUR_CODE"
        )
    }


@router.get("/token")
def exchange_token(code: str = Query(..., description="Authorization code from Strava OAuth redirect")):
    """
    Exchange an authorization code for access and refresh tokens.
    
    Use this after visiting the authorization URL and getting the code.
    Returns the refresh token which should be saved as STRAVA_REFRESH_TOKEN.
    """
    return exchange_code_for_token(code)


@router.get("/activities", response_model=List[StravaActivity])
def get_activities(
    per_page: int = Query(20, ge=1, le=50, description="Number of activities to return (max 50 to avoid rate limits)"),
    page: int = Query(1, ge=1, description="Page number"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type (e.g., Ride, Run, Walk)"),
    min_distance: Optional[float] = Query(None, ge=0, description="Minimum distance in meters"),
    max_distance: Optional[float] = Query(None, ge=0, description="Maximum distance in meters"),
    min_duration: Optional[int] = Query(None, ge=0, description="Minimum duration in seconds"),
    max_duration: Optional[int] = Query(None, ge=0, description="Maximum duration in seconds"),
    use_cache: bool = Query(True, description="Use cached results if available"),
) -> List[StravaActivity]:
    """
    Fetch recent Strava activities.
    
    Returns a list of activities sorted by start date (newest first).
    Uses caching to reduce API calls and avoid rate limiting.
    """
    return get_activities_controller(
        per_page=per_page,
        page=page,
        activity_type=activity_type,
        min_distance=min_distance,
        max_distance=max_distance,
        min_duration=min_duration,
        max_duration=max_duration,
        use_cache=use_cache,
    )

import os
import time
from datetime import datetime, timedelta
from typing import List, Optional
from functools import lru_cache

import requests
from fastapi import HTTPException

from .models import StravaActivity

# Simple in-memory cache for activities (expires after 5 minutes)
_activities_cache = {}
_cache_expiry = {}
CACHE_DURATION = 300  # 5 minutes

# Strava API credentials
# Set these via environment variables - DO NOT hardcode credentials
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN", "")

STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"


def get_access_token() -> str:
    """Get a new access token using the refresh token."""
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET or not STRAVA_REFRESH_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Strava credentials not configured. Please set STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN environment variables."
        )
    
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    
    try:
        response = requests.post(STRAVA_TOKEN_URL, data=payload, timeout=10)
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            raise HTTPException(
                status_code=401,
                detail=f"Strava token exchange failed ({response.status_code}): {err_json}"
            )
        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Strava token exchange succeeded but no access_token returned"
            )
        new_refresh = data.get("refresh_token")
        if new_refresh and new_refresh != STRAVA_REFRESH_TOKEN:
            import logging
            logger = logging.getLogger("uvicorn.error")
            logger.warning(
                "Strava returned a new refresh_token. Update your STRAVA_REFRESH_TOKEN env: %s",
                new_refresh,
            )
        return access_token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Strava access token: {str(e)}"
        ) from e


def get_authorization_url() -> str:
    """Generate Strava OAuth authorization URL with required scopes."""
    scopes = "activity:read_all"  # Request read access to all activities
    redirect_uri = "http://localhost:8000/api/v1/strava/callback"  # You may want to make this configurable
    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={STRAVA_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scopes}"
        f"&approval_prompt=force"
    )
    return auth_url


def exchange_code_for_token(code: str) -> dict:
    """
    Exchange an authorization code for access and refresh tokens.
    
    Args:
        code: Authorization code from Strava OAuth redirect
        
    Returns:
        Dictionary with token information
    """
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Strava credentials not configured. Please set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET environment variables."
        )
    
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }
    
    try:
        response = requests.post(STRAVA_TOKEN_URL, data=payload, timeout=10)
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            raise HTTPException(
                status_code=400,
                detail=f"Token exchange failed: {err_json}"
            )
        
        data = response.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_at": data.get("expires_at"),
            "expires_in": data.get("expires_in"),
            "token_type": data.get("token_type"),
            "athlete": data.get("athlete"),
            "message": "Save the refresh_token as your STRAVA_REFRESH_TOKEN environment variable"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange code: {str(e)}"
        ) from e


def clear_activities_cache() -> dict:
    """Clear the activities cache. Useful for testing."""
    global _activities_cache, _cache_expiry
    cache_size = len(_activities_cache)
    _activities_cache.clear()
    _cache_expiry.clear()
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"Cleared cache ({cache_size} entries)")
    return {
        "status": "ok",
        "message": f"Cleared {cache_size} cached entries"
    }


def get_activities(
    per_page: int = 20,
    page: int = 1,
    activity_type: Optional[str] = None,
    min_distance: Optional[float] = None,
    max_distance: Optional[float] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    use_cache: bool = True,
) -> List[StravaActivity]:
    """
    Fetch recent Strava activities.
    
    Args:
        per_page: Number of activities to return (max 50 to avoid rate limits)
        page: Page number
        activity_type: Filter by activity type (e.g., Ride, Run, Walk)
        min_distance: Minimum distance in meters
        max_distance: Maximum distance in meters
        min_duration: Minimum duration in seconds
        max_duration: Maximum duration in seconds
        use_cache: Use cached results if available
    
    Returns:
        List of StravaActivity objects sorted by start date (newest first)
    """
    import logging
    logger = logging.getLogger("uvicorn.error")
    
    # Check cache first (unless disabled)
    cache_key = f"{per_page}_{page}_{activity_type}_{min_distance}_{max_distance}_{min_duration}_{max_duration}"
    if use_cache and cache_key in _activities_cache:
        cache_time = _cache_expiry.get(cache_key, 0)
        if time.time() < cache_time:
            logger.info(f"Returning cached activities for key: {cache_key}")
            return _activities_cache[cache_key]
        else:
            # Cache expired, remove it
            _activities_cache.pop(cache_key, None)
            _cache_expiry.pop(cache_key, None)
    elif not use_cache:
        logger.info("Cache disabled for this request")
    
    try:
        # Get access token
        access_token = get_access_token()
        logger.info("Successfully obtained Strava access token")
        
        # Fetch activities
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "per_page": min(per_page, 50),  # Limit to 50 to avoid rate limits
            "page": page,
        }
        
        # Add activity type filter if provided (Strava API uses "type" parameter)
        # This filters at the API level, reducing the number of activities returned
        if activity_type:
            params["type"] = activity_type
            logger.info(f"Filtering activities by type: {activity_type}")
        
        url = f"{STRAVA_API_BASE}/athlete/activities"
        logger.info(f"Fetching Strava activities from {url} with params: {params}")
        
        # Note: The summary response from /athlete/activities includes:
        # - Basic map data (map.id, map.summary_polyline) - no need to fetch details for maps
        # - Photos summary (photos.count) - but not actual photo URLs, need detail fetch for photos
        params["include_all_efforts"] = "false"
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            logger.error(f"Strava activities request failed ({response.status_code}): {err_json}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Strava activities request failed ({response.status_code}): {err_json}"
            )
        
        activities_data = response.json()
        logger.info(f"Received {len(activities_data)} activities from Strava")
        
        # Convert to our model and apply filters
        activities = []
        for activity_data in activities_data:
            try:
                activity_id = activity_data.get("id")
                
                # Only fetch detailed activity if photos are indicated in the summary
                # This reduces API calls and avoids rate limiting (429 errors)
                photo_thumbnail_url = None
                photos_summary = activity_data.get("photos", {})
                has_photos_indicator = False
                
                # Log photos summary for debugging
                logger.debug(f"Activity {activity_id} photos_summary: {photos_summary}")
                
                if isinstance(photos_summary, dict):
                    photo_count = photos_summary.get("count", 0)
                    has_photos_indicator = photo_count > 0
                    logger.debug(f"Activity {activity_id} has {photo_count} photos (dict)")
                elif isinstance(photos_summary, list) and len(photos_summary) > 0:
                    has_photos_indicator = True
                    logger.debug(f"Activity {activity_id} has {len(photos_summary)} photos (list)")
                elif photos_summary:
                    # Might be a different structure
                    logger.debug(f"Activity {activity_id} photos_summary type: {type(photos_summary)}, value: {photos_summary}")
                
                # Only fetch detailed activity if we know there are photos
                # Map data should already be in the list response, so we don't need to fetch for maps
                if has_photos_indicator:
                    try:
                        # Add a small delay to avoid rate limiting
                        time.sleep(0.1)  # 100ms delay between detail fetches
                        
                        detail_url = f"{STRAVA_API_BASE}/activities/{activity_id}"
                        detail_response = requests.get(detail_url, headers=headers, timeout=10)
                        
                        if detail_response.status_code == 429:
                            logger.warning(f"Rate limited when fetching activity {activity_id}, stopping photo fetches")
                            break  # Stop fetching details to avoid more rate limits
                        elif detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            # Extract photo thumbnail
                            photos = detail_data.get("photos", {})
                            if photos:
                                if isinstance(photos, dict):
                                    # Check for primary photo
                                    primary = photos.get("primary")
                                    if primary and isinstance(primary, dict):
                                        urls = primary.get("urls", {})
                                        photo_thumbnail_url = urls.get("100") or urls.get("600") or primary.get("url")
                                elif isinstance(photos, list) and len(photos) > 0:
                                    # List of photos - get first one
                                    first_photo = photos[0]
                                    if isinstance(first_photo, dict):
                                        urls = first_photo.get("urls", {})
                                        photo_thumbnail_url = urls.get("100") or urls.get("600") or first_photo.get("url")
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 429:
                            logger.warning(f"Rate limited, stopping photo fetches for remaining activities")
                            break  # Stop fetching details to avoid more rate limits
                        else:
                            logger.warning(f"Error fetching photos for activity {activity_id}: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error fetching photos for activity {activity_id}: {str(e)}")
                
                # Prepare photos data for response
                photos_data = activity_data.get("photos", {})
                if photo_thumbnail_url:
                    # We successfully fetched a photo thumbnail
                    photos_data = {
                        "thumbnail_url": photo_thumbnail_url,
                        "has_photos": True,
                        "count": photos_summary.get("count", 1) if isinstance(photos_summary, dict) else 1
                    }
                elif isinstance(photos_data, dict):
                    # Keep original structure and add thumbnail_url if we have it
                    if photos_data.get("count", 0) > 0:
                        photos_data["has_photos"] = True
                        # Try to extract thumbnail from the summary if available
                        if not photos_data.get("thumbnail_url") and "primary" in photos_data:
                            primary = photos_data.get("primary", {})
                            if isinstance(primary, dict):
                                urls = primary.get("urls", {})
                                if urls:
                                    photos_data["thumbnail_url"] = urls.get("100") or urls.get("600")
                elif isinstance(photos_data, list) and len(photos_data) > 0:
                    # If it's a list, convert to our format
                    first_photo = photos_data[0]
                    if isinstance(first_photo, dict):
                        urls = first_photo.get("urls", {})
                        photos_data = {
                            "thumbnail_url": urls.get("100") or urls.get("600") or first_photo.get("url"),
                            "has_photos": True,
                            "count": len(photos_data),
                            "data": photos_data
                        }
                elif not photos_data or (isinstance(photos_data, dict) and photos_data.get("count", 0) == 0):
                    photos_data = None
                
                activity = StravaActivity(
                    id=activity_id,
                    name=activity_data.get("name", "Untitled Activity"),
                    type=activity_data.get("type", "Unknown"),
                    distance=activity_data.get("distance", 0),
                    moving_time=activity_data.get("moving_time", 0),
                    elapsed_time=activity_data.get("elapsed_time", 0),
                    total_elevation_gain=activity_data.get("total_elevation_gain"),
                    start_date=activity_data.get("start_date", ""),
                    start_date_local=activity_data.get("start_date_local", ""),
                    timezone=activity_data.get("timezone", ""),
                    average_speed=activity_data.get("average_speed"),
                    max_speed=activity_data.get("max_speed"),
                    average_cadence=activity_data.get("average_cadence"),
                    average_watts=activity_data.get("average_watts"),
                    weighted_average_watts=activity_data.get("weighted_average_watts"),
                    kilojoules=activity_data.get("kilojoules"),
                    device_watts=activity_data.get("device_watts"),
                    has_heartrate=activity_data.get("has_heartrate"),
                    average_heartrate=activity_data.get("average_heartrate"),
                    max_heartrate=activity_data.get("max_heartrate"),
                    calories=activity_data.get("calories"),
                    map=activity_data.get("map"),
                    photos=photos_data if photos_data else None,
                    description=activity_data.get("description"),
                    gear_id=activity_data.get("gear_id"),
                    gear=activity_data.get("gear"),
                )
                
                # Apply filters
                if activity_type and activity.type.lower() != activity_type.lower():
                    continue
                
                if min_distance is not None and activity.distance < min_distance:
                    continue
                
                if max_distance is not None and activity.distance > max_distance:
                    continue
                
                if min_duration is not None and activity.moving_time < min_duration:
                    continue
                
                if max_duration is not None and activity.moving_time > max_duration:
                    continue
                
                activities.append(activity)
            except Exception as e:
                logger.warning(f"Error parsing activity {activity_data.get('id')}: {str(e)}")
                continue
        
        logger.info(f"Returning {len(activities)} activities (after filtering)")
        
        # Cache the results
        if use_cache:
            _activities_cache[cache_key] = activities
            _cache_expiry[cache_key] = time.time() + CACHE_DURATION
            logger.info(f"Cached activities for key: {cache_key}")
        
        return activities
        
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Strava API request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Strava activities: {str(e)}"
        ) from e
    except Exception as exc:
        logger.error(f"Unexpected error fetching Strava activities: {str(exc)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Strava activities: {str(exc)}"
        ) from exc

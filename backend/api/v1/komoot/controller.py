import os
import time
from typing import List, Optional
from datetime import datetime

import requests
import logging

from .models import KomootCollection, KomootTour

logger = logging.getLogger("uvicorn.error")

# Try to use komPYoot library if available
try:
    from komPYoot.api import API as KomootAPI
    KOMOOT_LIBRARY_AVAILABLE = True
except ImportError:
    KOMOOT_LIBRARY_AVAILABLE = False

# Try to use PyMoot library if available (alternative with better highlight support)
try:
    from pymoot.connector import Connector as PyMootConnector
    PYMOOT_LIBRARY_AVAILABLE = True
except ImportError:
    PYMOOT_LIBRARY_AVAILABLE = False

# Simple in-memory cache for tours (expires after 5 minutes)
_tours_cache = {}
_cache_expiry = {}
CACHE_DURATION = 300  # 5 minutes

# Komoot API credentials
# Note: Komoot doesn't have an official public API, so we use unofficial methods
# You'll need to provide your Komoot email and password, or use a session token
# Set these via environment variables - DO NOT hardcode credentials
KOMOOT_EMAIL = os.getenv("KOMOOT_EMAIL", "")
KOMOOT_PASSWORD = os.getenv("KOMOOT_PASSWORD", "")
KOMOOT_USER_ID = os.getenv("KOMOOT_USER_ID", "")

# Komoot API base URLs (unofficial)
KOMOOT_API_BASE = "https://www.komoot.com/api/v007"
KOMOOT_AUTH_URL = "https://account.komoot.com/v1/signin"


def get_komoot_session() -> Optional[requests.Session]:
    """
    Authenticate with Komoot and return a session.
    Note: This uses unofficial API methods.
    """
    if not KOMOOT_EMAIL or not KOMOOT_PASSWORD:
        return None
    
    session = requests.Session()
    
    try:
        # Authenticate with Komoot
        auth_data = {
            "email": KOMOOT_EMAIL,
            "password": KOMOOT_PASSWORD,
        }
        
        response = session.post(KOMOOT_AUTH_URL, json=auth_data, timeout=10)
        
        if response.status_code == 200:
            return session
        else:
            return None
    except Exception as e:
        return None


def clear_cache() -> dict:
    """Clear the Komoot tours and collections cache."""
    _tours_cache.clear()
    _cache_expiry.clear()
    return {"message": "Cache cleared"}


def get_tours(
    per_page: int = 20,
    page: int = 1,
    tour_type: Optional[str] = None,
    use_cache: bool = True,
) -> List[KomootTour]:
    """
    Fetch Komoot tours.
    
    Note: Komoot doesn't have an official public API. This endpoint uses
    unofficial methods that may require authentication.
    
    Args:
        per_page: Number of tours to return
        page: Page number
        tour_type: Filter by tour type (e.g., bike, hike)
        use_cache: Use cached results if available
    
    Returns:
        List of KomootTour objects
    """
    # Check cache first
    cache_key = f"{per_page}_{page}_{tour_type}"
    if use_cache and cache_key in _tours_cache:
        cache_time = _cache_expiry.get(cache_key, 0)
        if time.time() < cache_time:
            logger.info(f"Returning cached tours for key: {cache_key}")
            return _tours_cache[cache_key]
        else:
            _tours_cache.pop(cache_key, None)
            _cache_expiry.pop(cache_key, None)
    
    if not KOMOOT_USER_ID:
        logger.warning("KOMOOT_USER_ID not configured. Please set KOMOOT_USER_ID environment variable.")
        # Return empty list instead of error - allows frontend to show helpful message
        return []
    
    try:
        # Try using komPYoot library first if available and credentials are provided
        if KOMOOT_LIBRARY_AVAILABLE and KOMOOT_EMAIL and KOMOOT_PASSWORD:
            try:
                logger.info("Attempting to use komPYoot library to fetch tours")
                api = KomootAPI()
                if api.login(KOMOOT_EMAIL, KOMOOT_PASSWORD):
                    logger.info("Successfully authenticated with Komoot")
                    tours_list = api.get_user_tours_list()
                    logger.info(f"Retrieved {len(tours_list)} tours from komPYoot library")
                    
                    # Convert komPYoot format to our format
                    tours = []
                    for tour_data in tours_list:
                        try:
                            # Filter by type if specified
                            if tour_type and tour_data.get("type", "").lower() != tour_type.lower():
                                continue
                            
                            # Extract difficulty - can be a string or dict with 'grade' key
                            difficulty_value = tour_data.get("difficulty")
                            if isinstance(difficulty_value, dict):
                                difficulty_value = difficulty_value.get("grade") or difficulty_value.get("difficulty") or str(difficulty_value)
                            elif difficulty_value is not None:
                                difficulty_value = str(difficulty_value)
                            
                            tour = KomootTour(
                                id=tour_data.get("id", 0),
                                name=tour_data.get("name", "Unnamed Tour"),
                                type=tour_data.get("type"),
                                distance=tour_data.get("distance"),
                                duration=tour_data.get("duration"),
                                elevation_gain=tour_data.get("elevation_gain"),
                                elevation_loss=tour_data.get("elevation_loss"),
                                difficulty=difficulty_value,
                                surface=tour_data.get("surface"),
                                created_at=tour_data.get("created_at"),
                                updated_at=tour_data.get("updated_at"),
                                map_image_url=tour_data.get("map_image_url") or tour_data.get("thumbnail_url"),
                                thumbnail_url=tour_data.get("thumbnail_url") or tour_data.get("map_image_url"),
                                komoot_url=f"https://www.komoot.com/tour/{tour_data.get('id')}" if tour_data.get('id') else None,
                                description=tour_data.get("description"),
                                highlights=tour_data.get("highlights", []),
                            )
                            tours.append(tour)
                        except Exception as e:
                            logger.warning(f"Error parsing tour {tour_data.get('id')}: {str(e)}")
                            continue
                    
                    # Apply pagination
                    start_idx = (page - 1) * per_page
                    end_idx = start_idx + per_page
                    tours = tours[start_idx:end_idx]
                    
                    # Cache the results
                    _tours_cache[cache_key] = tours
                    _cache_expiry[cache_key] = time.time() + CACHE_DURATION
                    
                    logger.info(f"Returning {len(tours)} Komoot tours from library")
                    return tours
                else:
                    logger.warning("komPYoot library login failed, falling back to direct API")
            except Exception as e:
                logger.warning(f"Error using komPYoot library: {str(e)}, falling back to direct API")
        
        # Fallback to direct API calls
        # Try different URL formats as the API structure may vary
        urls_to_try = [
            f"{KOMOOT_API_BASE}/users/{KOMOOT_USER_ID}/tours/",  # With trailing slash
            f"{KOMOOT_API_BASE}/users/{KOMOOT_USER_ID}/tours",    # Without trailing slash
            f"https://www.komoot.de/api/v007/users/{KOMOOT_USER_ID}/tours/",  # .de domain
            f"https://www.komoot.de/api/v007/users/{KOMOOT_USER_ID}/tours",   # .de domain no slash
        ]
        
        params = {
            "limit": per_page,
            "offset": (page - 1) * per_page,
        }
        
        # Try with session first, fallback to direct request
        session = get_komoot_session()
        response = None
        last_error = None
        
        for url in urls_to_try:
            try:
                logger.info(f"Trying Komoot API URL: {url}")
                if session:
                    response = session.get(url, params=params, timeout=15)
                else:
                    # Add headers to mimic browser request
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "application/json",
                    }
                    response = requests.get(url, params=params, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    logger.info(f"Successfully connected to Komoot API: {url}")
                    break
                elif response.status_code != 404:
                    # If we get a different error (like 401), that means the endpoint exists
                    logger.warning(f"Komoot API returned {response.status_code} for {url}")
                    break
            except Exception as e:
                last_error = str(e)
                logger.debug(f"Error trying {url}: {last_error}")
                continue
        
        if not response:
            logger.error(f"Could not connect to any Komoot API endpoint. Last error: {last_error}")
            logger.info("Tip: Try using komPYoot library by setting KOMOOT_EMAIL and KOMOOT_PASSWORD environment variables")
            return []
        
        if response.status_code == 404:
            logger.warning(f"Komoot API endpoint not found (404). This may indicate:")
            logger.warning("1. The API endpoint structure has changed")
            logger.warning("2. Authentication is required (try setting KOMOOT_EMAIL and KOMOOT_PASSWORD)")
            logger.warning("3. The user ID is incorrect")
            return []
        
        if response.status_code == 200:
            data = response.json()
            tours_data = data.get("tours", []) if isinstance(data, dict) else data
            
            tours = []
            for tour_data in tours_data:
                try:
                    # Filter by type if specified
                    if tour_type and tour_data.get("type", "").lower() != tour_type.lower():
                        continue
                    
                    # Extract map image URL if available
                    map_image_url = None
                    if "map" in tour_data:
                        map_obj = tour_data.get("map", {})
                        map_image_url = map_obj.get("image_url") or map_obj.get("thumbnail_url")
                    
                    # Build Komoot URL
                    tour_id = tour_data.get("id")
                    komoot_url = f"https://www.komoot.com/tour/{tour_id}" if tour_id else None
                    
                    # Extract difficulty - can be a string or dict with 'grade' key
                    difficulty_value = tour_data.get("difficulty")
                    if isinstance(difficulty_value, dict):
                        difficulty_value = difficulty_value.get("grade") or difficulty_value.get("difficulty") or str(difficulty_value)
                    elif difficulty_value is not None:
                        difficulty_value = str(difficulty_value)
                    
                    tour = KomootTour(
                        id=tour_data.get("id", 0),
                        name=tour_data.get("name", "Unnamed Tour"),
                        type=tour_data.get("type"),
                        distance=tour_data.get("distance"),
                        duration=tour_data.get("duration"),
                        elevation_gain=tour_data.get("elevation_gain"),
                        elevation_loss=tour_data.get("elevation_loss"),
                        difficulty=difficulty_value,
                        surface=tour_data.get("surface"),
                        created_at=tour_data.get("created_at"),
                        updated_at=tour_data.get("updated_at"),
                        map_image_url=map_image_url,
                        thumbnail_url=tour_data.get("thumbnail_url") or map_image_url,
                        komoot_url=komoot_url,
                        description=tour_data.get("description"),
                        highlights=tour_data.get("highlights", []),
                    )
                    tours.append(tour)
                except Exception as e:
                    logger.warning(f"Error parsing tour {tour_data.get('id')}: {str(e)}")
                    continue
            
            # Cache the results
            _tours_cache[cache_key] = tours
            _cache_expiry[cache_key] = time.time() + CACHE_DURATION
            
            logger.info(f"Returning {len(tours)} Komoot tours")
            return tours
        else:
            logger.error(f"Komoot API request failed ({response.status_code}): {response.text}")
            # Return empty list instead of error for now, as API is unofficial
            return []
            
    except Exception as e:
        logger.error(f"Error fetching Komoot tours: {str(e)}")
        # Return empty list instead of error
        return []


def get_collections(
    use_cache: bool = True,
) -> List[KomootCollection]:
    """
    Fetch Komoot collections.
    
    Collections are groups of tours, highlights, or routes that users organize.
    Note: This uses unofficial API methods and may require authentication.
    
    Args:
        use_cache: Use cached results if available
    
    Returns:
        List of KomootCollection objects
    """
    # Check cache first
    cache_key = "collections"
    if use_cache and cache_key in _tours_cache:
        cache_time = _cache_expiry.get(cache_key, 0)
        if time.time() < cache_time:
            logger.info(f"Returning cached collections")
            return _tours_cache[cache_key]
        else:
            _tours_cache.pop(cache_key, None)
            _cache_expiry.pop(cache_key, None)
    
    if not KOMOOT_EMAIL or not KOMOOT_PASSWORD:
        logger.warning("KOMOOT_EMAIL and KOMOOT_PASSWORD required for collections. Returning empty list.")
        return []
    
    try:
        collections = []
        
        # Try PyMoot first (better highlight/collection support)
        if PYMOOT_LIBRARY_AVAILABLE:
            try:
                logger.info("Attempting to fetch collections using PyMoot library")
                connector = PyMootConnector(email=KOMOOT_EMAIL, password=KOMOOT_PASSWORD)
                
                # PyMoot doesn't have explicit collections method, but we can try to get user data
                # Collections might be accessible through the API directly
                logger.info("PyMoot connected, but collections may need direct API access")
            except Exception as e:
                logger.warning(f"PyMoot library error: {str(e)}, trying alternative methods")
        
        # Try komPYoot library
        if KOMOOT_LIBRARY_AVAILABLE and not collections:
            try:
                logger.info("Attempting to fetch collections using komPYoot library")
                api = KomootAPI()
                if api.login(KOMOOT_EMAIL, KOMOOT_PASSWORD):
                    # Check if komPYoot has collections method
                    # This may not be available in all versions
                    if hasattr(api, 'get_collections'):
                        collections_data = api.get_collections()
                        logger.info(f"Retrieved {len(collections_data)} collections from komPYoot")
                        
                        for coll_data in collections_data:
                            collection = KomootCollection(
                                id=str(coll_data.get("id", "")),
                                name=coll_data.get("name", "Unnamed Collection"),
                                description=coll_data.get("description"),
                                item_count=coll_data.get("item_count") or len(coll_data.get("items", [])),
                                created_at=coll_data.get("created_at"),
                                updated_at=coll_data.get("updated_at"),
                                thumbnail_url=coll_data.get("thumbnail_url"),
                                komoot_url=f"https://www.komoot.com/collection/{coll_data.get('id')}" if coll_data.get('id') else None,
                                items=coll_data.get("items", []),
                            )
                            collections.append(collection)
            except Exception as e:
                logger.warning(f"komPYoot library error: {str(e)}")
        
        # Fallback: Try direct API call for collections
        if not collections:
            logger.info("Trying direct API call for collections")
            # Collections endpoint structure (unofficial)
            urls_to_try = [
                f"{KOMOOT_API_BASE}/users/{KOMOOT_USER_ID}/collections",
                f"{KOMOOT_API_BASE}/users/{KOMOOT_USER_ID}/collections/",
                f"https://www.komoot.de/api/v007/users/{KOMOOT_USER_ID}/collections",
            ]
            
            session = get_komoot_session()
            for url in urls_to_try:
                try:
                    logger.info(f"Trying collections URL: {url}")
                    if session:
                        response = session.get(url, timeout=15)
                    else:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                            "Accept": "application/json",
                        }
                        response = requests.get(url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        collections_data = data.get("collections", []) if isinstance(data, dict) else data
                        
                        for coll_data in collections_data:
                            collection = KomootCollection(
                                id=str(coll_data.get("id", "")),
                                name=coll_data.get("name", "Unnamed Collection"),
                                description=coll_data.get("description"),
                                item_count=coll_data.get("item_count") or len(coll_data.get("items", [])),
                                created_at=coll_data.get("created_at"),
                                updated_at=coll_data.get("updated_at"),
                                thumbnail_url=coll_data.get("thumbnail_url"),
                                komoot_url=f"https://www.komoot.com/collection/{coll_data.get('id')}" if coll_data.get('id') else None,
                                items=coll_data.get("items", []),
                            )
                            collections.append(collection)
                        break
                except Exception as e:
                    logger.debug(f"Error trying {url}: {str(e)}")
                    continue
        
        # Cache the results
        if collections:
            _tours_cache[cache_key] = collections
            _cache_expiry[cache_key] = time.time() + CACHE_DURATION
        
        logger.info(f"Returning {len(collections)} Komoot collections")
        return collections
        
    except Exception as e:
        logger.error(f"Error fetching Komoot collections: {str(e)}")
        return []

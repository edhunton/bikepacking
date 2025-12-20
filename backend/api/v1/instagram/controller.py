import os
import time
from typing import List, Optional
import logging

import requests
from fastapi import HTTPException

from .models import InstagramMedia, InstagramUser

logger = logging.getLogger("uvicorn.error")

# Simple in-memory cache for media (expires after 5 minutes)
_media_cache = {}
_cache_expiry = {}
CACHE_DURATION = 300  # 5 minutes

# Instagram API credentials
# Set these via environment variables - DO NOT hardcode credentials
# Read dynamically to pick up changes without restart
def _get_env(key: str, default: str = "") -> str:
    """Get environment variable, reading fresh each time."""
    return os.getenv(key, default)

INSTAGRAM_APP_ID = _get_env("INSTAGRAM_APP_ID", "")
INSTAGRAM_APP_SECRET = _get_env("INSTAGRAM_APP_SECRET", "")
INSTAGRAM_CLIENT_TOKEN = _get_env("INSTAGRAM_CLIENT_TOKEN", "")  # For server-to-server
INSTAGRAM_APP_TOKEN = _get_env("INSTAGRAM_APP_TOKEN", "")  # App token (format: APP_ID|APP_SECRET)

# Access token and user ID - read dynamically in functions
def get_access_token() -> str:
    """Get access token, reading fresh from environment."""
    return _get_env("INSTAGRAM_ACCESS_TOKEN", "").strip()

def get_user_id() -> str:
    """Get user ID, reading fresh from environment."""
    return _get_env("INSTAGRAM_USER_ID", "").strip()

def get_instagram_account_id_from_token() -> Optional[str]:
    """
    Extract Instagram Business Account ID from the access token's granular scopes.
    This is the most reliable way to get the correct Instagram account ID.
    """
    access_token = get_access_token()
    if not access_token:
        return None
    
    try:
        url = "https://graph.facebook.com/v24.0/debug_token"
        params = {
            "input_token": access_token,
            "access_token": access_token,
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            granular_scopes = data.get("data", {}).get("granular_scopes", [])
            for scope in granular_scopes:
                if scope.get("scope") == "instagram_basic":
                    target_ids = scope.get("target_ids", [])
                    if target_ids:
                        return target_ids[0]  # Return first Instagram account ID
    except Exception as e:
        logger.warning(f"Error extracting Instagram account ID from token: {str(e)}")
    
    return None

# Instagram Graph API base URL
# Use Facebook Graph API instead of graph.instagram.com for better token compatibility
INSTAGRAM_API_BASE = "https://graph.facebook.com/v24.0"


def get_authorization_url() -> str:
    """Generate Instagram OAuth authorization URL."""
    if not INSTAGRAM_APP_ID:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_APP_ID not configured. Please set it as an environment variable."
        )
    
    redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/api/v1/instagram/callback")
    # For Instagram Graph API (Business accounts), use Facebook OAuth instead
    # For Basic Display API, use Instagram OAuth
    scopes = "user_profile,user_media"
    
    auth_url = (
        f"https://api.instagram.com/oauth/authorize"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes}"
        f"&response_type=code"
    )
    return auth_url


def get_facebook_authorization_url() -> str:
    """Generate Facebook OAuth authorization URL for Instagram Graph API."""
    if not INSTAGRAM_APP_ID:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_APP_ID not configured. Please set it as an environment variable."
        )
    
    redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/api/v1/instagram/callback")
    # Required permissions for Instagram Graph API
    scopes = "pages_read_engagement,pages_show_list,instagram_basic,business_management"
    
    auth_url = (
        f"https://www.facebook.com/v24.0/dialog/oauth"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes}"
        f"&response_type=code"
    )
    return auth_url


def exchange_code_for_token(code: str) -> dict:
    """
    Exchange an authorization code for access token.
    
    Args:
        code: Authorization code from Instagram OAuth redirect
        
    Returns:
        Dictionary with token information
    """
    if not INSTAGRAM_APP_ID or not INSTAGRAM_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Instagram credentials not configured. Please set INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET environment variables."
        )
    
    redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/api/v1/instagram/callback")
    
    payload = {
        "client_id": INSTAGRAM_APP_ID,
        "client_secret": INSTAGRAM_APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": code,
    }
    
    try:
        response = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data=payload,
            timeout=10
        )
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
        access_token = data.get("access_token")
        user_id = data.get("user_id")
        
        # Also get user info to verify the token works
        user_info = None
        if access_token and user_id:
            try:
                # Get user info to verify token
                user_url = f"{INSTAGRAM_API_BASE}/{user_id}"
                user_params = {
                    "fields": "id,username",
                    "access_token": access_token,
                }
                user_response = requests.get(user_url, params=user_params, timeout=10)
                if user_response.status_code == 200:
                    user_info = user_response.json()
            except Exception as e:
                logger.warning(f"Could not fetch user info: {str(e)}")
        
        return {
            "access_token": access_token,
            "user_id": user_id,
            "user_info": user_info,
            "message": (
                f"Save these values in your .env file:\n"
                f"INSTAGRAM_ACCESS_TOKEN={access_token}\n"
                f"INSTAGRAM_USER_ID={user_id}"
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange code: {str(e)}"
        ) from e


def exchange_short_lived_for_long_lived(short_lived_token: str) -> dict:
    """
    Exchange a short-lived access token for a long-lived token (60 days).
    
    This is used for server-to-server authentication with Instagram Graph API.
    
    Args:
        short_lived_token: Short-lived access token from Graph API Explorer
        
    Returns:
        Dictionary with long-lived token information
    """
    if not INSTAGRAM_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_APP_SECRET not configured. Required for token exchange."
        )
    
    url = f"{INSTAGRAM_API_BASE}/access_token"
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": INSTAGRAM_APP_SECRET,
        "access_token": short_lived_token,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
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
            "token_type": data.get("token_type", "bearer"),
            "expires_in": data.get("expires_in"),  # Usually 5184000 seconds (60 days)
            "message": "Save the access_token as your INSTAGRAM_ACCESS_TOKEN environment variable"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange token: {str(e)}"
        ) from e


def refresh_access_token() -> str:
    """
    Refresh the long-lived access token.
    
    Returns:
        New access token
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_ACCESS_TOKEN not configured."
        )
    
    url = f"{INSTAGRAM_API_BASE}/refresh_access_token"
    params = {
        "grant_type": "ig_refresh_token",
        "access_token": access_token,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            raise HTTPException(
                status_code=401,
                detail=f"Token refresh failed: {err_json}"
            )
        
        data = response.json()
        new_token = data.get("access_token")
        if not new_token:
            raise HTTPException(
                status_code=401,
                detail="Token refresh succeeded but no access_token returned"
            )
        return new_token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh token: {str(e)}"
        ) from e


def clear_media_cache() -> dict:
    """Clear the media cache. Useful for testing."""
    global _media_cache, _cache_expiry
    cache_size = len(_media_cache)
    _media_cache.clear()
    _cache_expiry.clear()
    logger.info(f"Cleared cache ({cache_size} entries)")
    return {
        "status": "ok",
        "message": f"Cleared {cache_size} cached entries"
    }


def get_page_access_token(page_id: str) -> Optional[str]:
    """
    Get Page Access Token for a specific Facebook Page.
    Required for accessing page information and connected Instagram accounts.
    """
    access_token = get_access_token()
    if not access_token:
        return None
    
    try:
        # First get all pages the user manages
        url = "https://graph.facebook.com/v24.0/me/accounts"
        params = {
            "access_token": access_token,
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get("data", [])
            for page in pages:
                if page.get("id") == page_id:
                    return page.get("access_token")
    except Exception as e:
        logger.warning(f"Error getting page access token: {str(e)}")
    
    return None


def get_user_pages() -> dict:
    """
    Get list of Facebook Pages the user manages.
    Useful for finding page IDs and their connected Instagram accounts.
    """
    access_token = get_access_token()
    if not access_token:
        return {
            "success": False,
            "error": "INSTAGRAM_ACCESS_TOKEN not configured"
        }
    
    try:
        url = "https://graph.facebook.com/v24.0/me/accounts"
        params = {
            "fields": "id,name,instagram_business_account,connected_instagram_account",
            "access_token": access_token,
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get("data", [])
            return {
                "success": True,
                "pages": pages,
                "count": len(pages)
            }
        else:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            return {
                "success": False,
                "error": err_json,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_instagram_account_from_page(page_id: str, use_page_token: bool = True, access_token: Optional[str] = None) -> dict:
    """
    Get Instagram account connected to a Facebook Page.
    
    Args:
        page_id: Facebook Page ID
        use_page_token: If True, try to get and use Page Access Token (recommended)
        
    Returns:
        Dictionary with result and Instagram account information
    """
    configured_token = get_access_token()
    if not configured_token and not access_token:
        return {
            "success": False,
            "error": "INSTAGRAM_ACCESS_TOKEN not configured"
        }
    
    # Use provided token or fall back to configured token
    token_to_use = access_token or configured_token
    if not token_to_use:
        return {
            "success": False,
            "error": "No access token provided. Set INSTAGRAM_ACCESS_TOKEN or provide token parameter."
        }
    
    # Try to get Page Access Token if requested
    final_token = token_to_use
    if use_page_token:
        try:
            # Use the provided/configured token to get page token
            page_token = get_page_access_token(page_id)
            if page_token:
                final_token = page_token
                logger.info(f"Using Page Access Token for page {page_id}")
            else:
                logger.warning(f"Could not get Page Access Token, using provided User Token")
        except Exception as e:
            logger.warning(f"Error getting page token: {str(e)}, using provided token")
    
    try:
        url = f"https://graph.facebook.com/v24.0/{page_id}"
        params = {
            "fields": "connected_instagram_account",
            "access_token": final_token,
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            instagram_account = data.get("connected_instagram_account")
            if instagram_account:
                return {
                    "success": True,
                    "instagram_account": instagram_account,
                    "instagram_account_id": instagram_account.get("id"),
                    "page_id": page_id,
                    "full_response": data
                }
            else:
                return {
                    "success": False,
                    "error": "No connected Instagram account found",
                    "page_id": page_id,
                    "full_response": data
                }
        else:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            return {
                "success": False,
                "error": err_json,
                "status_code": response.status_code,
                "page_id": page_id
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "page_id": page_id
        }


def get_instagram_business_account_id() -> Optional[str]:
    """
    Get Instagram Business Account ID.
    
    For accounts connected to personal Facebook profiles, tries multiple methods:
    1. From Facebook Pages (if any pages exist)
    2. From /me/accounts endpoint
    3. Direct query if we have the account ID
    """
    access_token = get_access_token()
    if not access_token:
        return None
    
    try:
        # Method 1: Try to get from pages the user manages
        pages_url = "https://graph.facebook.com/me/accounts"
        pages_params = {
            "access_token": access_token,
            "fields": "id,name,instagram_business_account",
        }
        pages_response = requests.get(pages_url, params=pages_params, timeout=10)
        
        if pages_response.status_code == 200:
            pages_data = pages_response.json()
            pages = pages_data.get("data", [])
            for page in pages:
                instagram_account = page.get("instagram_business_account")
                if instagram_account:
                    account_id = instagram_account.get("id")
                    if account_id:
                        logger.info(f"Found Instagram Business Account ID from page: {account_id}")
                        return account_id
        
        # Method 2: Try to get from /me endpoint with instagram_accounts field
        me_url = "https://graph.facebook.com/v24.0/me"
        me_params = {
            "fields": "instagram_accounts{id,username}",
            "access_token": access_token,
        }
        me_response = requests.get(me_url, params=me_params, timeout=10)
        if me_response.status_code == 200:
            me_data = me_response.json()
            instagram_accounts = me_data.get("instagram_accounts", {})
            if isinstance(instagram_accounts, dict):
                accounts_list = instagram_accounts.get("data", [])
            elif isinstance(instagram_accounts, list):
                accounts_list = instagram_accounts
            else:
                accounts_list = []
            
            if accounts_list:
                account_id = accounts_list[0].get("id")
                if account_id:
                    logger.info(f"Found Instagram Account ID from /me: {account_id}")
                    return account_id
        
        # Method 3: If user has provided a page ID, try to get from that page
        # (This would be called separately via the /page/{page_id}/instagram endpoint)
        
    except Exception as e:
        logger.warning(f"Error getting Instagram Business Account ID: {str(e)}")
    
    return None


def debug_access_token() -> dict:
    """
    Debug access token to see what app ID it's associated with.
    
    Returns:
        Dictionary with token information
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_ACCESS_TOKEN not configured."
        )
    
    try:
        # Use Facebook Graph API debug_token endpoint (works better than Instagram's)
        url = "https://graph.facebook.com/v24.0/debug_token"
        params = {
            "input_token": access_token,
            "access_token": access_token,
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "token_info": data.get("data", {}),
                "configured_app_id": INSTAGRAM_APP_ID,
                "token_app_id": data.get("data", {}).get("app_id", "unknown"),
                "match": data.get("data", {}).get("app_id") == INSTAGRAM_APP_ID,
            }
        else:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            return {
                "error": err_json,
                "configured_app_id": INSTAGRAM_APP_ID,
            }
    except Exception as e:
        return {
            "error": str(e),
            "configured_app_id": INSTAGRAM_APP_ID,
        }


def get_user_info() -> InstagramUser:
    """
    Get Instagram user information.
    
    Returns:
        InstagramUser object
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="Instagram credentials not configured. Please set INSTAGRAM_ACCESS_TOKEN environment variable."
        )
    
    # Try to extract from token's granular scopes first (most reliable)
    instagram_id = get_instagram_account_id_from_token()
    if instagram_id:
        user_id = instagram_id
        logger.info(f"Using Instagram Business Account ID from token: {user_id}")
    else:
        user_id = get_user_id()
        # If user_id is not provided or is invalid (not numeric), try to get it from Facebook Page
        if not user_id or not user_id.isdigit():
            business_account_id = get_instagram_business_account_id()
            if business_account_id:
                user_id = business_account_id
                logger.info(f"Using Instagram Business Account ID from Facebook Page: {user_id}")
            else:
                # Final fallback: Try /me endpoint (won't work with Facebook Graph API for Instagram)
                raise HTTPException(
                    status_code=500,
                    detail="Could not retrieve Instagram Business Account ID. Please set INSTAGRAM_USER_ID (must be numeric Instagram Business Account ID) in your .env file, or ensure your token has instagram_basic permission."
                )
    
    url = f"{INSTAGRAM_API_BASE}/{user_id}"
    # Use Facebook Graph API fields (account_type not available, use business_discovery for more info)
    params = {
        "fields": "id,username,media_count",
        "access_token": access_token,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            logger.error(f"Instagram user info request failed ({response.status_code}): {err_json}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Instagram user info request failed: {err_json}"
            )
        
        data = response.json()
        # account_type not available via Facebook Graph API for Instagram
        return InstagramUser(
            id=data.get("id", ""),
            username=data.get("username", ""),
            account_type="BUSINESS",  # Assume business if we can access it via Graph API
            media_count=data.get("media_count"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Instagram user info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Instagram user info: {str(e)}"
        ) from e


def get_media(
    limit: int = 25,
    after: Optional[str] = None,
    media_type: Optional[str] = None,
    use_cache: bool = True,
) -> List[InstagramMedia]:
    """
    Fetch Instagram media/posts.
    
    Args:
        limit: Number of media items to return (max 100)
        after: Pagination cursor (from previous response)
        media_type: Filter by media type (IMAGE, VIDEO, CAROUSEL_ALBUM)
        use_cache: Use cached results if available
    
    Returns:
        List of InstagramMedia objects
    """
    access_token = get_access_token()
    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="Instagram credentials not configured. Please set INSTAGRAM_ACCESS_TOKEN environment variable."
        )
    
    # Get user ID - try from token's granular scopes first (most reliable), then env, then Facebook Page, then /me endpoint
    # Always try to extract from token first as it's the most accurate
    instagram_id = get_instagram_account_id_from_token()
    if instagram_id:
        user_id = instagram_id
        logger.info(f"Using Instagram Business Account ID from token: {user_id}")
    else:
        user_id = get_user_id()
        logger.info(f"Using Instagram User ID from env: {user_id}")
    
    # If still no user_id, try to get from Facebook Page
    if not user_id or not user_id.isdigit():
        business_account_id = get_instagram_business_account_id()
        if business_account_id:
            user_id = business_account_id
            logger.info(f"Using Instagram Business Account ID from Facebook Page: {user_id}")
    
    # Final fallback: Try /me endpoint
    if not user_id or not user_id.isdigit():
        try:
            me_url = f"{INSTAGRAM_API_BASE}/me"
            me_params = {
                "fields": "id",
                "access_token": access_token,
            }
            me_response = requests.get(me_url, params=me_params, timeout=10)
            if me_response.status_code == 200:
                me_data = me_response.json()
                user_id = me_data.get("id")
                logger.info(f"Retrieved user ID from /me endpoint: {user_id}")
            else:
                try:
                    err_json = me_response.json()
                except Exception:
                    err_json = me_response.text
                logger.error(f"/me endpoint failed ({me_response.status_code}): {err_json}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not retrieve user ID. Error: {err_json}. Please set INSTAGRAM_USER_ID (must be numeric) in your .env file."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calling /me endpoint: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Could not retrieve user ID: {str(e)}. Please set INSTAGRAM_USER_ID (must be numeric) in your .env file."
            )
    
    # Check cache first
    cache_key = f"{limit}_{after}_{media_type}"
    if use_cache and cache_key in _media_cache:
        cache_time = _cache_expiry.get(cache_key, 0)
        if time.time() < cache_time:
            logger.info(f"Returning cached media for key: {cache_key}")
            return _media_cache[cache_key]
        else:
            _media_cache.pop(cache_key, None)
            _cache_expiry.pop(cache_key, None)
    elif not use_cache:
        logger.info("Cache disabled for this request")
    
    try:
        url = f"{INSTAGRAM_API_BASE}/{user_id}/media"
        # Facebook Graph API fields for Instagram media
        params = {
            "fields": "id,caption,media_type,media_url,permalink,timestamp",
            "access_token": access_token,
            "limit": min(limit, 100),  # Instagram API max is 100
        }
        
        if after:
            params["after"] = after
        
        logger.info(f"Fetching Instagram media from {url}")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            logger.error(f"Instagram media request failed ({response.status_code}): {err_json}")
            
            # Provide helpful error message for common issues
            error_detail = f"Instagram media request failed: {err_json}"
            if isinstance(err_json, dict) and err_json.get("error", {}).get("code") == 190:
                error_detail += (
                    f"\n\nTroubleshooting: The access token doesn't match your App ID ({INSTAGRAM_APP_ID}). "
                    f"Please ensure:\n"
                    f"1. The token was generated for the same app as INSTAGRAM_APP_ID\n"
                    f"2. Use /api/v1/instagram/debug/token to check token info\n"
                    f"3. Generate a new token using /api/v1/instagram/authorize if needed"
                )
            
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
        
        data = response.json()
        media_data_list = data.get("data", [])
        logger.info(f"Received {len(media_data_list)} media items from Instagram")
        
        media_items = []
        for item_data in media_data_list:
            try:
                # Filter by media type if specified
                if media_type and item_data.get("media_type", "").upper() != media_type.upper():
                    continue
                
                # Get children for carousel albums
                children = None
                if item_data.get("media_type") == "CAROUSEL_ALBUM":
                    children = _get_carousel_children(item_data.get("id"))
                
                media = InstagramMedia(
                    id=item_data.get("id", ""),
                    caption=item_data.get("caption"),
                    media_type=item_data.get("media_type", "IMAGE"),
                    media_url=item_data.get("media_url"),
                    thumbnail_url=item_data.get("thumbnail_url"),  # May not be available via Facebook Graph API
                    permalink=item_data.get("permalink"),
                    timestamp=item_data.get("timestamp"),
                    username=None,  # Not available in media response via Facebook Graph API
                    like_count=None,  # Not available in basic media response
                    comments_count=None,  # Not available in basic media response
                    children=children,
                )
                media_items.append(media)
            except Exception as e:
                logger.warning(f"Error parsing media {item_data.get('id')}: {str(e)}")
                continue
        
        logger.info(f"Returning {len(media_items)} media items (after filtering)")
        
        # Cache the results
        if use_cache:
            _media_cache[cache_key] = media_items
            _cache_expiry[cache_key] = time.time() + CACHE_DURATION
            logger.info(f"Cached media for key: {cache_key}")
        
        return media_items
        
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Instagram API request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Instagram media: {str(e)}"
        ) from e
    except Exception as exc:
        logger.error(f"Unexpected error fetching Instagram media: {str(exc)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Instagram media: {str(exc)}"
        ) from exc


def _get_carousel_children(media_id: str) -> Optional[List[InstagramMedia]]:
    """Get children media items for a carousel album."""
    access_token = get_access_token()
    if not access_token or not media_id:
        return None
    
    try:
        url = f"{INSTAGRAM_API_BASE}/{media_id}/children"
        # Facebook Graph API fields for carousel children
        params = {
            "fields": "id,media_type,media_url",
            "access_token": access_token,
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            children_data = data.get("data", [])
            return [
                InstagramMedia(
                    id=child.get("id", ""),
                    media_type=child.get("media_type", "IMAGE"),
                    media_url=child.get("media_url"),
                    thumbnail_url=None,  # May not be available via Facebook Graph API
                )
                for child in children_data
            ]
    except Exception as e:
        logger.warning(f"Error fetching carousel children for {media_id}: {str(e)}")
    
    return None

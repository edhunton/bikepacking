import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .controller import (
    get_media as get_media_controller,
    get_user_info as get_user_info_controller,
    get_authorization_url,
    get_facebook_authorization_url,
    exchange_code_for_token,
    exchange_short_lived_for_long_lived,
    refresh_access_token,
    clear_media_cache,
    debug_access_token,
    get_instagram_account_from_page,
    get_user_pages,
)
from .models import InstagramMedia, InstagramUser

router = APIRouter()

# Instagram API credentials for authorization endpoint
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "")


@router.get("/health")
def health_check() -> dict[str, str]:
    """Lightweight endpoint to confirm the Instagram router is live."""
    return {"status": "ok"}


@router.post("/cache/clear")
def clear_cache() -> dict[str, str]:
    """Clear the media cache. Useful for testing."""
    return clear_media_cache()


@router.get("/authorize")
def get_authorize_url() -> dict[str, str]:
    """
    Get the Instagram OAuth authorization URL.

    Visit this URL to authorize the app and get an access token.
    After authorization, you'll receive a code that can be exchanged for tokens.
    """
    # Read from environment at request time to ensure .env is loaded
    app_id = os.getenv("INSTAGRAM_APP_ID", "")
    if not app_id:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_APP_ID not configured. Please set it as an environment variable."
        )
    
    return {
        "authorization_url": get_authorization_url(),
        "instructions": (
            "1. Visit the authorization_url above\n"
            "2. Authorize the app\n"
            "3. Copy the 'code' parameter from the redirect URL\n"
            "4. Exchange the code for tokens using /api/v1/instagram/token?code=YOUR_CODE"
        )
    }


@router.get("/authorize/facebook")
def get_facebook_authorize_url() -> dict[str, str]:
    """
    Get the Facebook OAuth authorization URL (for Instagram Graph API).
    
    This is for Instagram Business accounts. It requests permissions:
    - pages_read_engagement
    - pages_show_list
    - instagram_basic
    - business_management
    
    Visit this URL to authorize the app and get an access token.
    After authorization, you'll receive a code that can be exchanged for tokens.
    """
    app_id = os.getenv("INSTAGRAM_APP_ID", "")
    if not app_id:
        raise HTTPException(
            status_code=500,
            detail="INSTAGRAM_APP_ID not configured. Please set it as an environment variable."
        )
    
    return {
        "authorization_url": get_facebook_authorization_url(),
        "permissions": "pages_read_engagement,pages_show_list,instagram_basic,business_management",
        "instructions": (
            "1. Visit the authorization_url above\n"
            "2. Authorize the app with the requested permissions\n"
            "3. Copy the 'code' parameter from the redirect URL\n"
            "4. Exchange the code for tokens using /api/v1/instagram/token?code=YOUR_CODE\n"
            "5. Or use Graph API Explorer: https://developers.facebook.com/tools/explorer/"
        )
    }


@router.get("/token")
def exchange_token(code: str = Query(..., description="Authorization code from Instagram OAuth redirect")):
    """
    Exchange an authorization code for access token.
    
    Use this after visiting the authorization URL and getting the code.
    Returns the access token which should be saved as INSTAGRAM_ACCESS_TOKEN.
    """
    return exchange_code_for_token(code)


@router.get("/token/refresh")
def refresh_token() -> dict[str, str]:
    """
    Refresh the long-lived access token.
    
    Returns a new access token that should replace INSTAGRAM_ACCESS_TOKEN.
    """
    new_token = refresh_access_token()
    return {
        "access_token": new_token,
        "message": "Update your INSTAGRAM_ACCESS_TOKEN environment variable with the new token"
    }


@router.get("/token/exchange")
def exchange_token_endpoint(
    short_lived_token: str = Query(..., description="Short-lived access token from Graph API Explorer")
) -> dict:
    """
    Exchange a short-lived access token for a long-lived token (60 days).
    
    Use this for server-to-server authentication:
    1. Get a short-lived token from Graph API Explorer
    2. Call this endpoint to exchange it for a long-lived token
    3. Save the returned access_token as INSTAGRAM_ACCESS_TOKEN
    """
    return exchange_short_lived_for_long_lived(short_lived_token)


@router.get("/debug/token")
def debug_token() -> dict:
    """
    Debug the access token to see what app ID it's associated with.
    
    Useful for troubleshooting "Access token does not contain a valid app ID" errors.
    """
    return debug_access_token()


@router.get("/pages")
def list_pages() -> dict:
    """
    Get list of Facebook Pages you manage and their connected Instagram accounts.
    
    This helps you find the correct page ID and Instagram account ID.
    """
    return get_user_pages()


@router.get("/page/{page_id}/instagram")
def get_page_instagram_account(
    page_id: str,
    access_token: Optional[str] = Query(None, description="Optional: Override access token for this request")
) -> dict:
    """
    Get Instagram account connected to a Facebook Page.
    
    Example: GET /api/v1/instagram/page/***/instagram
    
    This calls: GET https://graph.facebook.com/v24.0/{page_id}?fields=connected_instagram_account
    
    You can optionally provide an access_token query parameter to test with a different token.
    """
    result = get_instagram_account_from_page(page_id, access_token=access_token)
    
    if result.get("success"):
        return {
            "success": True,
            "instagram_account": result.get("instagram_account"),
            "instagram_account_id": result.get("instagram_account_id"),
            "message": f"Found Instagram Account ID: {result.get('instagram_account_id')}. Set this as INSTAGRAM_USER_ID in your .env file."
        }
    else:
        return result


@router.get("/debug/find-account")
def find_account() -> dict:
    """
    Try to find the Instagram Business Account ID from Facebook Pages.
    Useful when you have a user token but need the Instagram account ID.
    """
    from .controller import get_instagram_business_account_id, get_access_token
    
    access_token = get_access_token()
    if not access_token:
        return {
            "error": "INSTAGRAM_ACCESS_TOKEN not configured",
            "configured": False
        }
    
    account_id = get_instagram_business_account_id()
    if account_id:
        return {
            "success": True,
            "instagram_account_id": account_id,
            "message": f"Found Instagram Account ID: {account_id}. Set this as INSTAGRAM_USER_ID in your .env file."
        }
    else:
        return {
            "success": False,
            "message": "Could not find Instagram Business Account ID. Make sure your Instagram account is connected to a Facebook Page, or set INSTAGRAM_USER_ID manually."
        }


@router.get("/debug/test-token")
def test_token() -> dict:
    """
    Test the access token by calling the /me endpoint.
    Useful for debugging token issues.
    """
    import os
    from .controller import get_access_token, INSTAGRAM_API_BASE
    import requests
    
    access_token = get_access_token()
    if not access_token:
        return {
            "error": "INSTAGRAM_ACCESS_TOKEN not configured",
            "configured": False
        }
    
    try:
        me_url = f"{INSTAGRAM_API_BASE}/me"
        me_params = {
            "fields": "id,username",
            "access_token": access_token,
        }
        response = requests.get(me_url, params=me_params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "user_id": data.get("id"),
                "username": data.get("username"),
                "message": f"Token is valid! User ID: {data.get('id')}"
            }
        else:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            return {
                "success": False,
                "status_code": response.status_code,
                "error": err_json,
                "message": "Token test failed. Check the error details above."
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error testing token: {str(e)}"
        }


@router.get("/debug/app")
def debug_app() -> dict:
    """
    Debug app configuration to help troubleshoot "Invalid platform app" errors.
    
    Returns information about the configured App ID and provides guidance.
    """
    app_id = os.getenv("INSTAGRAM_APP_ID", "")
    redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/api/v1/instagram/callback")
    
    return {
        "configured_app_id": app_id,
        "redirect_uri": redirect_uri,
        "instructions": (
            "For Instagram Graph API (Business accounts):\n"
            "1. Use your Facebook App ID (this is correct for Graph API)\n"
            "2. Get a User Access Token from Graph API Explorer with permissions:\n"
            "   - pages_read_engagement\n"
            "   - pages_show_list\n"
            "   - instagram_basic\n"
            "3. Make sure the token matches this App ID\n"
            "\n"
            "For Instagram Basic Display API (personal accounts):\n"
            "1. Go to Products > Instagram > Basic Display\n"
            "2. Find the 'Instagram App ID' (different from Facebook App ID)\n"
            "3. Use that Instagram App ID instead"
        ),
        "authorization_url": get_authorization_url() if app_id else "App ID not configured",
    }


@router.get("/user", response_model=InstagramUser)
def get_user() -> InstagramUser:
    """
    Get Instagram user information.
    
    Returns basic information about the authenticated Instagram user.
    """
    return get_user_info_controller()


@router.get("/media", response_model=List[InstagramMedia])
def get_media(
    limit: int = Query(25, ge=1, le=100, description="Number of media items to return (max 100)"),
    after: Optional[str] = Query(None, description="Pagination cursor from previous response"),
    media_type: Optional[str] = Query(None, description="Filter by media type (IMAGE, VIDEO, CAROUSEL_ALBUM)"),
    use_cache: bool = Query(True, description="Use cached results if available"),
) -> List[InstagramMedia]:
    """
    Fetch Instagram media/posts.
    
    Returns a list of media items sorted by timestamp (newest first).
    Uses caching to reduce API calls and avoid rate limiting.
    """
    return get_media_controller(
        limit=limit,
        after=after,
        media_type=media_type,
        use_cache=use_cache,
    )

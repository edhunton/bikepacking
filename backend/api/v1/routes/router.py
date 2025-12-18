import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from typing import List
from fastapi.responses import FileResponse

from .controller import get_all_routes, get_route_by_id, create_route, update_route, delete_route, save_gpx_file
from .db import get_connection
from .models import Route, CreateRoute, UpdateRoute, RoutePhoto, CreateRoutePhoto
from .photos import save_route_photo, list_route_photos, delete_route_photo, reprocess_route_photos_gps, reprocess_route_photos_gps

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Lightweight endpoint to confirm the routes router is live."""
    return {"status": "ok"}


@router.get("/", response_model=List[Route])
def get_routes(
    guidebook_id: Optional[int] = Query(
        None,
        description="Filter by guidebook ID. Use null or omit for routes not in guidebooks."
    ),
    country: Optional[str] = Query(
        None,
        description="Filter by country"
    ),
    county: Optional[str] = Query(
        None,
        description="Filter by county"
    ),
    include_deleted: bool = Query(
        False,
        description="Include deleted routes (where live = False)"
    ),
) -> List[Route]:
    """
    Get all routes with optional filtering.
    
    Returns a list of routes that can be filtered by:
    - guidebook_id: Routes from a specific guidebook (null for routes not in guidebooks)
    - country: Filter by country
    - county: Filter by county
    - include_deleted: Include routes where live = False (default: False)
    """
    return get_all_routes(
        guidebook_id=guidebook_id,
        country=country,
        county=county,
        include_deleted=include_deleted,
    )


@router.get("/{route_id}", response_model=Route)
def get_route(route_id: int) -> Route:
    """
    Get a single route by ID.
    
    Args:
        route_id: The route ID
        
    Returns:
        Route object
    """
    return get_route_by_id(route_id)


@router.post("/", response_model=Route, status_code=201)
def create_new_route(route: CreateRoute) -> Route:
    """
    Create a new route.
    
    Args:
        route: Route data to create
        
    Returns:
        Created Route object with ID
    """
    return create_route(route)


@router.put("/{route_id}", response_model=Route)
def update_existing_route(route_id: int, route: UpdateRoute) -> Route:
    """
    Update an existing route.
    
    Args:
        route_id: The route ID to update
        route: Route data to update (only provided fields will be updated)
        
    Returns:
        Updated Route object
    """
    return update_route(route_id, route)


@router.delete("/{route_id}")
def delete_existing_route(route_id: int) -> dict:
    """
    Delete an existing route (soft delete - sets live = False).
    
    Args:
        route_id: The route ID to delete
        
    Returns:
        Dictionary with success message
    """
    return delete_route(route_id)


@router.patch("/{route_id}/toggle-live")
def toggle_route_live_status(route_id: int) -> Route:
    """
    Toggle the live status of a route (restore if deleted, or delete if live).
    
    Args:
        route_id: The route ID to toggle
        
    Returns:
        Updated Route object
    """
    # Get current route status
    existing_route = get_route_by_id(route_id, include_deleted=True)
    
    # Get current live status
    query_check = "SELECT live FROM routes WHERE id = %s;"
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query_check, (route_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Route not found")
                current_live_status = row[0]
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error checking route status: {str(exc)}") from exc
    
    # Toggle the status
    new_live_status = not current_live_status
    
    query = """
        UPDATE routes 
        SET live = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, title, gpx_url, thumbnail_url, country, county, distance,
                  ascent, descent, starting_station, ending_station, getting_there,
                  bike_choice, guidebook_id, min_time, max_time, off_road_distance, off_road_percentage, grade,
                  description, strava_activities, google_mymap_url, komoot_collections,
                  created_at, updated_at;
    """
    
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (new_live_status, route_id))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Route not found")
                conn.commit()
        except HTTPException:
            raise
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error toggling route status: {str(exc)}") from exc

    return Route(
        id=row[0],
        title=row[1],
        gpx_url=row[2],
        thumbnail_url=row[3],
        country=row[4],
        county=row[5],
        distance=float(row[6]) if row[6] is not None else None,
        ascent=row[7],
        descent=row[8],
        starting_station=row[9],
        ending_station=row[10],
        getting_there=row[11],
        bike_choice=row[12],
        guidebook_id=row[13],
        min_time=float(row[14]) if row[14] is not None else None,
        max_time=float(row[15]) if row[15] is not None else None,
        off_road_distance=float(row[16]) if row[16] is not None else None,
        off_road_percentage=float(row[17]) if row[17] is not None else None,
        grade=row[18],
        description=row[19],
        strava_activities=row[20],
        google_mymap_url=row[21],
        komoot_collections=row[22],
        created_at=row[23].isoformat() if row[23] else None,
        updated_at=row[24].isoformat() if row[24] else None,
    )


@router.post("/upload-gpx")
async def upload_gpx_file(file: UploadFile = File(...)) -> dict:
    """
    Upload a GPX file.
    
    Args:
        file: The GPX file to upload
        
    Returns:
        Dictionary with the file URL/path
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not file.filename.lower().endswith('.gpx'):
        raise HTTPException(status_code=400, detail="File must be a .gpx file")
    
    # Save file
    file_path = save_gpx_file(file)
    
    # Return the URL path with localhost:5173 prefix for local development
    # The frontend Vite proxy will forward /static requests to the backend
    filename = Path(file_path).name
    return {
        "filename": file.filename,
        "url": f"http://localhost:5173/static/gpx/{filename}",
        "message": "File uploaded successfully"
    }


@router.get("/gpx/{filename}")
def get_gpx_file(filename: str):
    """
    Serve a GPX file.
    
    Args:
        filename: The GPX filename
        
    Returns:
        GPX file
    """
    # Security: ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = Path(__file__).parent.parent.parent.parent / "static" / "gpx" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="GPX file not found")
    
    return FileResponse(
        file_path,
        media_type="application/gpx+xml",
        filename=filename
    )


@router.post("/download-gpx")
async def download_gpx_from_url(gpx_url: str = Query(..., description="URL of the GPX file to download")) -> dict:
    """
    Download a GPX file from an external URL and save it locally.
    This is useful for importing routes from external sources like Strava.
    If the URL is from Strava, it will use Strava API credentials for authentication.
    
    Args:
        gpx_url: The URL of the GPX file to download
        
    Returns:
        Dictionary with the local file URL/path
    """
    import requests
    import uuid
    from pathlib import Path
    
    try:
        # Check if this is a Strava URL and use authentication if available
        headers = {}
        if "strava.com" in gpx_url and "/activities/" in gpx_url:
            try:
                # Import Strava controller to get access token
                from api.v1.strava.controller import get_access_token
                access_token = get_access_token()
                headers["Authorization"] = f"Bearer {access_token}"
            except Exception as auth_err:
                # If auth fails, try without it (might work for public activities)
                print(f"Warning: Could not get Strava access token, trying without auth: {auth_err}")
        
        # Download the GPX file
        response = requests.get(gpx_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Validate it's a GPX file (check content type or file extension)
        content_type = response.headers.get("content-type", "").lower()
        if "gpx" not in content_type and "xml" not in content_type:
            # Check if URL ends with .gpx or /export_gpx
            if not gpx_url.lower().endswith(".gpx") and not gpx_url.lower().endswith("/export_gpx"):
                raise HTTPException(status_code=400, detail="URL does not appear to be a GPX file")
        
        # Get the static directory path
        backend_dir = Path(__file__).parent.parent.parent.parent
        gpx_dir = backend_dir / "static" / "gpx"
        gpx_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}.gpx"
        file_path = gpx_dir / unique_filename
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        # Return the URL path
        return {
            "filename": unique_filename,
            "url": f"http://localhost:5173/static/gpx/{unique_filename}",
            "message": "GPX file downloaded and saved successfully"
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download GPX file from URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing GPX file: {str(e)}")


@router.post("/{route_id}/generate-thumbnail")
def generate_thumbnail(route_id: int, force: bool = False):
    """
    Generate a thumbnail for a route from its GPX file.
    
    Args:
        route_id: The route ID
        force: If True, regenerate even if thumbnail exists
        
    Returns:
        Dictionary with thumbnail URL
    """
    from .controller import generate_route_thumbnail
    
    try:
        thumbnail_path = generate_route_thumbnail(route_id, force_regenerate=force)
        return {
            "message": "Thumbnail generated successfully",
            "thumbnail_url": thumbnail_path
        }
    except HTTPException as e:
        # Re-raise with more context
        print(f"HTTPException for route {route_id}: {e.status_code} - {e.detail}")
        raise
    except Exception as exc:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating thumbnail for route {route_id}: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating thumbnail: {str(exc)}. Check server logs for details."
        ) from exc


@router.get("/{route_id}/photos", response_model=List[RoutePhoto])
def list_photos(route_id: int) -> List[RoutePhoto]:
    """List photos for a route."""
    return list_route_photos(route_id)


@router.post("/photos", response_model=RoutePhoto)
def upload_photo(
    route_id: int = Form(...),
    caption: str | None = Form(None),
    file: UploadFile = File(...),
) -> RoutePhoto:
    """Upload a photo for a route."""
    return save_route_photo(file, route_id, caption)


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int):
    """Delete a route photo by ID."""
    return delete_route_photo(photo_id)


@router.post("/{route_id}/photos/reprocess-gps")
def reprocess_photos_gps(route_id: int):
    """
    Re-process all photos for a route to extract GPS coordinates from EXIF data.
    Only processes photos that don't already have GPS coordinates.
    """
    updated_photos = reprocess_route_photos_gps(route_id)
    return {
        "message": f"Processed {len(updated_photos)} photos with GPS data",
        "updated_count": len(updated_photos),
        "photos": [photo.dict() for photo in updated_photos]
    }

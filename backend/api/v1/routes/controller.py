import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import gpxpy
import polyline
import requests
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from PIL import Image

from .db import get_connection
from .models import Route, CreateRoute, UpdateRoute

# Load environment variables
# Load from backend/.env file (same directory as server.py)
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
# Strip surrounding whitespace/quotes to avoid malformed tokens
MAPBOX_ACCESS_TOKEN = (os.getenv("MAPBOX_ACCESS_TOKEN", "") or "").strip().strip('"').rstrip(".")


def get_all_routes(
    guidebook_id: Optional[int] = None,
    country: Optional[str] = None,
    county: Optional[str] = None,
    difficulty: Optional[str] = None,
    include_deleted: bool = False,
) -> List[Route]:
    """
    Retrieve all routes from the database with optional filtering.
    
    Args:
        guidebook_id: Filter by guidebook ID (None for routes not in guidebooks)
        country: Filter by country
        county: Filter by county
        difficulty: Filter by difficulty
        include_deleted: If True, include routes where live = False
        
    Returns:
        List of Route objects
        
    Raises:
        HTTPException: If database query fails
    """
    query = """
        SELECT id, title, gpx_url, thumbnail_url, difficulty, country, county, distance,
               ascent, descent, starting_station, ending_station, getting_there,
               bike_choice, guidebook_id, created_at, updated_at
        FROM routes
        WHERE 1=1
    """
    params = []
    
    # Filter by live status (only show live routes by default)
    if not include_deleted:
        query += " AND live = TRUE"
    
    if guidebook_id is not None:
        query += " AND guidebook_id = %s"
        params.append(guidebook_id)
    
    if country:
        query += " AND country = %s"
        params.append(country)
    
    if county:
        query += " AND county = %s"
        params.append(county)
    
    if difficulty:
        query += " AND difficulty = %s"
        params.append(difficulty)
    
    query += " ORDER BY title;"
    
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Error querying routes") from exc

    return [
        Route(
            id=row[0],
            title=row[1],
            gpx_url=row[2],
            thumbnail_url=row[3],
            difficulty=row[4],
            country=row[5],
            county=row[6],
            distance=float(row[7]) if row[7] is not None else None,
            ascent=row[8],
            descent=row[9],
            starting_station=row[10],
            ending_station=row[11],
            getting_there=row[12],
            bike_choice=row[13],
            guidebook_id=row[14],
            created_at=row[15].isoformat() if row[15] else None,
            updated_at=row[16].isoformat() if row[16] else None,
        )
        for row in rows
    ]


def get_route_by_id(route_id: int, include_deleted: bool = True) -> Route:
    """
    Retrieve a single route by ID.
    
    Args:
        route_id: The route ID
        include_deleted: If True, can retrieve routes where live = False
        
    Returns:
        Route object
        
    Raises:
        HTTPException: If route not found or database query fails
    """
    query = """
        SELECT id, title, gpx_url, thumbnail_url, difficulty, country, county, distance,
               ascent, descent, starting_station, ending_station, getting_there,
               bike_choice, guidebook_id, created_at, updated_at
        FROM routes
        WHERE id = %s
    """
    params = [route_id]
    
    if not include_deleted:
        query += " AND live = TRUE"
    
    query += ";"
    
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                row = cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Route not found")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Error querying route") from exc

    return Route(
        id=row[0],
        title=row[1],
        gpx_url=row[2],
        thumbnail_url=row[3],
        difficulty=row[4],
        country=row[5],
        county=row[6],
        distance=float(row[7]) if row[7] is not None else None,
        ascent=row[8],
        descent=row[9],
        starting_station=row[10],
        ending_station=row[11],
        getting_there=row[12],
        bike_choice=row[13],
        guidebook_id=row[14],
        created_at=row[15].isoformat() if row[15] else None,
        updated_at=row[16].isoformat() if row[16] else None,
    )


def create_route(route_data: CreateRoute) -> Route:
    """
    Create a new route in the database.
    
    Args:
        route_data: CreateRoute object with route information
        
    Returns:
        Created Route object with ID
        
    Raises:
        HTTPException: If database insert fails
    """
    query = """
        INSERT INTO routes (
            title, gpx_url, thumbnail_url, difficulty, country, county, distance,
            ascent, descent, starting_station, ending_station, getting_there,
            bike_choice, guidebook_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, title, gpx_url, thumbnail_url, difficulty, country, county, distance,
                  ascent, descent, starting_station, ending_station, getting_there,
                  bike_choice, guidebook_id, created_at, updated_at;
    """
    
    params = (
        route_data.title,
        route_data.gpx_url,
        None,  # thumbnail_url will be generated later if needed
        route_data.difficulty,
        route_data.country,
        route_data.county,
        route_data.distance,
        route_data.ascent,
        route_data.descent,
        route_data.starting_station,
        route_data.ending_station,
        route_data.getting_there,
        route_data.bike_choice,
        route_data.guidebook_id,
    )
    
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                conn.commit()
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating route: {str(exc)}") from exc

    new_route = Route(
        id=row[0],
        title=row[1],
        gpx_url=row[2],
        thumbnail_url=row[3],
        difficulty=row[4],
        country=row[5],
        county=row[6],
        distance=float(row[7]) if row[7] is not None else None,
        ascent=row[8],
        descent=row[9],
        starting_station=row[10],
        ending_station=row[11],
        getting_there=row[12],
        bike_choice=row[13],
        guidebook_id=row[14],
        created_at=row[15].isoformat() if row[15] else None,
        updated_at=row[16].isoformat() if row[16] else None,
    )

    # Auto-generate thumbnail when a GPX file is provided
    if new_route.gpx_url:
        try:
            generate_route_thumbnail(new_route.id, force_regenerate=True)
            # Return the freshest data (with thumbnail_url) after generation
            return get_route_by_id(new_route.id, include_deleted=True)
        except Exception as exc:  # pragma: no cover - best-effort thumbnail creation
            # Do not fail route creation if thumbnail generation fails
            print(f"Warning: failed to generate thumbnail for route {new_route.id}: {exc}")

    return new_route


def save_gpx_file(file: UploadFile) -> str:
    """
    Save an uploaded GPX file to the static/gpx directory.
    
    Args:
        file: The uploaded file
        
    Returns:
        Path to the saved file
        
    Raises:
        HTTPException: If file save fails
    """
    # Get the static directory path
    backend_dir = Path(__file__).parent.parent.parent.parent
    gpx_dir = backend_dir / "static" / "gpx"
    
    # Create directory if it doesn't exist
    gpx_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a unique filename to avoid conflicts
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = gpx_dir / unique_filename
    
    try:
        # Read file content
        content = file.file.read()
        
        # Write to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        return str(file_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error saving GPX file: {str(exc)}") from exc


def update_route(route_id: int, route_data: UpdateRoute) -> Route:
    """
    Update an existing route in the database.
    
    Args:
        route_id: The route ID to update
        route_data: UpdateRoute object with fields to update
        
    Returns:
        Updated Route object
        
    Raises:
        HTTPException: If route not found or database update fails
    """
    # First check if route exists (including deleted routes)
    existing_route = get_route_by_id(route_id, include_deleted=True)
    gpx_changed = False
    
    # Build dynamic UPDATE query based on provided fields
    updates = []
    params = []
    
    if route_data.title is not None:
        updates.append("title = %s")
        params.append(route_data.title)
    if route_data.gpx_url is not None:
        updates.append("gpx_url = %s")
        params.append(route_data.gpx_url)
        gpx_changed = route_data.gpx_url != existing_route.gpx_url
    if route_data.thumbnail_url is not None:
        updates.append("thumbnail_url = %s")
        params.append(route_data.thumbnail_url)
    if route_data.difficulty is not None:
        updates.append("difficulty = %s")
        params.append(route_data.difficulty)
    if route_data.country is not None:
        updates.append("country = %s")
        params.append(route_data.country)
    if route_data.county is not None:
        updates.append("county = %s")
        params.append(route_data.county)
    if route_data.distance is not None:
        updates.append("distance = %s")
        params.append(route_data.distance)
    if route_data.ascent is not None:
        updates.append("ascent = %s")
        params.append(route_data.ascent)
    if route_data.descent is not None:
        updates.append("descent = %s")
        params.append(route_data.descent)
    if route_data.starting_station is not None:
        updates.append("starting_station = %s")
        params.append(route_data.starting_station)
    if route_data.ending_station is not None:
        updates.append("ending_station = %s")
        params.append(route_data.ending_station)
    if route_data.getting_there is not None:
        updates.append("getting_there = %s")
        params.append(route_data.getting_there)
    if route_data.bike_choice is not None:
        updates.append("bike_choice = %s")
        params.append(route_data.bike_choice)
    if route_data.guidebook_id is not None:
        updates.append("guidebook_id = %s")
        params.append(route_data.guidebook_id)
    if route_data.live is not None:
        updates.append("live = %s")
        params.append(route_data.live)
    
    if not updates:
        # No fields to update, return existing route
        return existing_route
    
    # Add updated_at timestamp
    updates.append("updated_at = CURRENT_TIMESTAMP")
    
    # Build query
    query = f"""
        UPDATE routes
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, title, gpx_url, thumbnail_url, difficulty, country, county, distance,
                  ascent, descent, starting_station, ending_station, getting_there,
                  bike_choice, guidebook_id, created_at, updated_at;
    """
    params.append(route_id)
    
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                conn.commit()
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating route: {str(exc)}") from exc

    updated_route = Route(
        id=row[0],
        title=row[1],
        gpx_url=row[2],
        thumbnail_url=row[3],
        difficulty=row[4],
        country=row[5],
        county=row[6],
        distance=float(row[7]) if row[7] is not None else None,
        ascent=row[8],
        descent=row[9],
        starting_station=row[10],
        ending_station=row[11],
        getting_there=row[12],
        bike_choice=row[13],
        guidebook_id=row[14],
        created_at=row[15].isoformat() if row[15] else None,
        updated_at=row[16].isoformat() if row[16] else None,
    )

    # If GPX changed, regenerate thumbnail (best-effort)
    if gpx_changed and updated_route.gpx_url:
        try:
            generate_route_thumbnail(route_id, force_regenerate=True)
            return get_route_by_id(route_id, include_deleted=True)
        except Exception as exc:  # pragma: no cover
            print(f"Warning: failed to regenerate thumbnail for route {route_id}: {exc}")

    return updated_route


def delete_route(route_id: int) -> dict:
    """
    Soft delete a route by setting live = False.
    The route remains in the database but is hidden from normal queries.
    Can be reinstated by manually setting live = TRUE in the database.
    
    Args:
        route_id: The route ID to delete
        
    Returns:
        Dictionary with success message
        
    Raises:
        HTTPException: If route not found or database update fails
    """
    # First check if route exists (including deleted routes)
    existing_route = get_route_by_id(route_id, include_deleted=True)
    
    # Check if already deleted
    query_check = "SELECT live FROM routes WHERE id = %s;"
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query_check, (route_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Route not found")
                if not row[0]:  # live is False
                    return {
                        "message": f"Route '{existing_route.title}' is already deleted",
                        "deleted_id": route_id,
                        "already_deleted": True
                    }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error checking route status: {str(exc)}") from exc
    
    # Soft delete the route
    query = """
        UPDATE routes 
        SET live = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id;
    """
    
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (route_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Route not found")
                conn.commit()
        except HTTPException:
            raise
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting route: {str(exc)}") from exc

    return {
        "message": f"Route '{existing_route.title}' deleted successfully (can be reinstated by setting live = TRUE in database)",
        "deleted_id": route_id
    }


def parse_gpx_coordinates(gpx_path: str) -> List[tuple]:
    """
    Parse a GPX file and extract coordinates.
    
    Args:
        gpx_path: Path to the GPX file
        
    Returns:
        List of (lon, lat) tuples
        
    Raises:
        HTTPException: If GPX file cannot be parsed
    """
    try:
        with open(gpx_path, 'r', encoding='utf-8') as f:
            gpx = gpxpy.parse(f)
        
        coordinates = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    coordinates.append((point.longitude, point.latitude))
        
        # If no track points, try waypoints
        if not coordinates:
            for waypoint in gpx.waypoints:
                coordinates.append((waypoint.longitude, waypoint.latitude))
        
        # If still no coordinates, try route points
        if not coordinates:
            for route in gpx.routes:
                for point in route.points:
                    coordinates.append((point.longitude, point.latitude))
        
        return coordinates
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error parsing GPX file: {str(exc)}") from exc


def generate_mapbox_static_image_url(coordinates: List[tuple], width: int = 192, height: int = 128) -> str:
    """
    Generate a Mapbox Static Images API URL for a route.
    
    Args:
        coordinates: List of (lon, lat) tuples
        width: Image width in pixels (default 192)
        height: Image height in pixels (default 128)
        
    Returns:
        URL string for the static image
        
    Raises:
        HTTPException: If Mapbox token is not configured
    """
    if not MAPBOX_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="Mapbox access token not configured")
    
    if not coordinates:
        raise HTTPException(status_code=400, detail="No coordinates found in GPX file")
    
    # Reduce coordinates to avoid URL length limits (414 error)
    # Mapbox Static Images API has URL length limits (~8192 chars), so we sample points
    # For thumbnails, we don't need all points - just enough to show the route shape
    max_points = 100  # Maximum points to include in URL (keeps URL under limit)
    if len(coordinates) > max_points:
        # Sample evenly across the route to preserve shape
        step = len(coordinates) // max_points
        sampled_coords = coordinates[::step]
        # Always include first and last point for accuracy
        if sampled_coords[-1] != coordinates[-1]:
            sampled_coords.append(coordinates[-1])
        coordinates = sampled_coords
    
    # Calculate bounds
    lngs = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]
    
    # Calculate center
    center_lng = (min(lngs) + max(lngs)) / 2
    center_lat = (min(lats) + max(lats)) / 2
    
    # Encode coordinates using polyline encoding (required by Mapbox Static Images API)
    # Polyline encoding is much more compact than raw coordinates
    # Convert to list of [lat, lon] tuples (polyline expects lat,lon order)
    polyline_coords = [[lat, lon] for lon, lat in coordinates]
    encoded_polyline = polyline.encode(polyline_coords)
    
    # Create path overlay: path-4+3b82f6 (4px width, blue color #3b82f6)
    # Format: path-{strokeWidth}+{strokeColor}({encoded-polyline})
    # Note: stroke-opacity is optional, we're using full opacity
    # URL-encode the overlay to avoid invalid characters
    path_overlay_raw = f"path-4+3b82f6({encoded_polyline})"
    path_overlay = quote(path_overlay_raw, safe="()+,")
    
    # Calculate zoom level based on bounds
    lng_span = max(lngs) - min(lngs)
    lat_span = max(lats) - min(lats)
    max_span = max(lng_span, lat_span)
    
    # Approximate zoom level (rough calculation)
    if max_span > 10:
        zoom = 4
    elif max_span > 5:
        zoom = 5
    elif max_span > 2:
        zoom = 6
    elif max_span > 1:
        zoom = 7
    elif max_span > 0.5:
        zoom = 8
    elif max_span > 0.25:
        zoom = 9
    elif max_span > 0.1:
        zoom = 10
    else:
        zoom = 11
    
    # Build URL with path overlay
    # Format: https://api.mapbox.com/styles/v1/{username}/{style_id}/static/{overlay}/auto/{width}x{height}?access_token={token}
    # Using 'auto' centers and zooms the map to fit the path automatically
    base_url = "https://api.mapbox.com/styles/v1/mapbox/outdoors-v12/static"
    url = f"{base_url}/{path_overlay}/auto/{width}x{height}?access_token={MAPBOX_ACCESS_TOKEN}"
    
    return url


def download_and_save_thumbnail(image_url: str, route_id: int) -> str:
    """
    Download a Mapbox static image, convert to WebP, and save it to static/thumbnails.
    
    Args:
        image_url: URL of the Mapbox static image
        route_id: Route ID for filename
        
    Returns:
        Relative path to the saved thumbnail (WebP format)
        
    Raises:
        HTTPException: If download, conversion, or save fails
    """
    backend_dir = Path(__file__).parent.parent.parent.parent
    thumbnail_dir = backend_dir / "static" / "thumbnails"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Check if we got an image
        if not response.content:
            raise HTTPException(status_code=500, detail="Empty response from Mapbox API")
        
        # Open image with PIL
        try:
            image = Image.open(BytesIO(response.content))
        except Exception as img_exc:
            # If image parsing fails, it might be an error response from Mapbox
            error_text = response.text[:200] if hasattr(response, 'text') else str(response.content[:200])
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to parse image from Mapbox. Response: {error_text}. Error: {str(img_exc)}"
            ) from img_exc
        
        # Convert RGBA to RGB if necessary (WebP supports both, but RGB is smaller)
        if image.mode == 'RGBA':
            # Create white background for transparency
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save as WebP with quality optimization
        # Quality 85 provides good balance between size and quality for thumbnails
        thumbnail_filename = f"route_{route_id}.webp"
        thumbnail_path = thumbnail_dir / thumbnail_filename
        
        image.save(thumbnail_path, 'WEBP', quality=85, method=6)
        
        # Return relative path for database storage
        return f"/static/thumbnails/{thumbnail_filename}"
    except HTTPException:
        raise
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500, 
            detail=f"Error downloading image from Mapbox: {str(exc)}. URL: {image_url[:100]}..."
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing thumbnail: {str(exc)}"
        ) from exc


def generate_route_thumbnail(route_id: int, force_regenerate: bool = False) -> str:
    """
    Generate a thumbnail for a route from its GPX file.
    
    Args:
        route_id: The route ID
        force_regenerate: If True, regenerate even if thumbnail exists
        
    Returns:
        Relative path to the thumbnail
        
    Raises:
        HTTPException: If route not found, GPX missing, or generation fails
    """
    # Get route
    route = get_route_by_id(route_id, include_deleted=True)
    
    # Check if thumbnail already exists
    if route.thumbnail_url and not force_regenerate:
        # Verify file exists
        backend_dir = Path(__file__).parent.parent.parent.parent
        thumbnail_path = backend_dir / route.thumbnail_url.lstrip("/")
        if thumbnail_path.exists():
            return route.thumbnail_url
    
    # Check if GPX file exists
    if not route.gpx_url:
        raise HTTPException(status_code=400, detail="Route has no GPX file")
    
    # Get GPX file path
    backend_dir = Path(__file__).parent.parent.parent.parent
    
    # Note: We handle http URLs in the path extraction below, so we don't need to check here
    
    # Extract filename from path
    # Handle both full URLs (http://localhost:5173/static/gpx/file.gpx) and relative paths (/static/gpx/file.gpx)
    gpx_url_clean = route.gpx_url
    if gpx_url_clean.startswith("http://") or gpx_url_clean.startswith("https://"):
        # Extract just the filename from URL
        # Example: http://localhost:5173/static/gpx/file.gpx -> file.gpx
        gpx_filename = gpx_url_clean.split("/")[-1]
        # For localhost URLs, we can still access the file locally
        if "localhost" in gpx_url_clean or "127.0.0.1" in gpx_url_clean:
            # It's a local file, extract the filename
            pass  # Already extracted above
        else:
            # External URL - not supported
            raise HTTPException(
                status_code=400, 
                detail=f"External GPX URLs not supported for thumbnail generation. URL: {gpx_url_clean}"
            )
    elif gpx_url_clean.startswith("/static/"):
        # Relative path like /static/gpx/file.gpx
        gpx_filename = gpx_url_clean.split("/")[-1]
    else:
        # Assume it's already just a filename
        gpx_filename = gpx_url_clean.split("/")[-1]
    
    gpx_path = backend_dir / "static" / "gpx" / gpx_filename
    
    if not gpx_path.exists():
        raise HTTPException(
            status_code=400, 
            detail=f"GPX file not found at: {gpx_path}. GPX URL was: {route.gpx_url}, extracted filename: {gpx_filename}. Checked path: {gpx_path}"
        )
    
    # Parse GPX to get coordinates
    coordinates = parse_gpx_coordinates(str(gpx_path))
    
    if not coordinates:
        raise HTTPException(status_code=400, detail="No coordinates found in GPX file")
    
    # Generate Mapbox static image URL
    image_url = generate_mapbox_static_image_url(coordinates)
    
    # Download and save thumbnail
    thumbnail_path = download_and_save_thumbnail(image_url, route_id)
    
    # Update route with thumbnail URL
    try:
        update_data = UpdateRoute(thumbnail_url=thumbnail_path)
        updated_route = update_route(route_id, update_data)
        print(f"Successfully updated route {route_id} with thumbnail_url: {thumbnail_path}")
    except Exception as exc:
        print(f"Error updating route {route_id} with thumbnail_url: {str(exc)}")
        # Don't fail the whole operation if DB update fails - file is already saved
        import traceback
        traceback.print_exc()
    
    return thumbnail_path

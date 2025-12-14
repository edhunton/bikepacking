import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, UploadFile

from .db import get_connection
from .models import Route, CreateRoute, UpdateRoute


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
        SELECT id, title, gpx_url, difficulty, country, county, distance,
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
            difficulty=row[3],
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
            created_at=row[14].isoformat() if row[14] else None,
            updated_at=row[15].isoformat() if row[15] else None,
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
        SELECT id, title, gpx_url, difficulty, country, county, distance,
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
        difficulty=row[3],
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
        created_at=row[14].isoformat() if row[14] else None,
        updated_at=row[15].isoformat() if row[15] else None,
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
            title, gpx_url, difficulty, country, county, distance,
            ascent, descent, starting_station, ending_station, getting_there,
            bike_choice, guidebook_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, title, gpx_url, difficulty, country, county, distance,
                  ascent, descent, starting_station, ending_station, getting_there,
                  bike_choice, guidebook_id, created_at, updated_at;
    """
    
    params = (
        route_data.title,
        route_data.gpx_url,
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

    return Route(
        id=row[0],
        title=row[1],
        gpx_url=row[2],
        difficulty=row[3],
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
        created_at=row[14].isoformat() if row[14] else None,
        updated_at=row[15].isoformat() if row[15] else None,
    )


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
    
    # Build dynamic UPDATE query based on provided fields
    updates = []
    params = []
    
    if route_data.title is not None:
        updates.append("title = %s")
        params.append(route_data.title)
    if route_data.gpx_url is not None:
        updates.append("gpx_url = %s")
        params.append(route_data.gpx_url)
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
        RETURNING id, title, gpx_url, difficulty, country, county, distance,
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

    return Route(
        id=row[0],
        title=row[1],
        gpx_url=row[2],
        difficulty=row[3],
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
        created_at=row[14].isoformat() if row[14] else None,
        updated_at=row[15].isoformat() if row[15] else None,
    )


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

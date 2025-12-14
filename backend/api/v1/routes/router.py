import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse

from .controller import get_all_routes, get_route_by_id, create_route, update_route, save_gpx_file
from .models import Route, CreateRoute, UpdateRoute

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
    difficulty: Optional[str] = Query(
        None,
        description="Filter by difficulty level"
    ),
) -> List[Route]:
    """
    Get all routes with optional filtering.
    
    Returns a list of routes that can be filtered by:
    - guidebook_id: Routes from a specific guidebook (null for routes not in guidebooks)
    - country: Filter by country
    - county: Filter by county
    - difficulty: Filter by difficulty level
    """
    return get_all_routes(
        guidebook_id=guidebook_id,
        country=country,
        county=county,
        difficulty=difficulty,
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

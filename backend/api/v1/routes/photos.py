import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile
from PIL import Image, ExifTags

from .db import get_connection
from .models import RoutePhoto, CreateRoutePhoto


def _extract_exif_coords(image: Image.Image):
    """Extract GPS coordinates and timestamp from EXIF data."""
    try:
        exif = image._getexif()  # type: ignore
        if not exif:
            return None, None, None
        gps_tag = None
        for k, v in ExifTags.TAGS.items():
            if v == "GPSInfo":
                gps_tag = k
                break
        if gps_tag is None or gps_tag not in exif:
            return None, None, None
        gps_info = exif[gps_tag]

        def _convert_to_deg(value):
            d = float(value[0][0]) / float(value[0][1])
            m = float(value[1][0]) / float(value[1][1])
            s = float(value[2][0]) / float(value[2][1])
            return d + (m / 60.0) + (s / 3600.0)

        lat = lng = None
        if 2 in gps_info and 4 in gps_info and 1 in gps_info and 3 in gps_info:
            lat = _convert_to_deg(gps_info[2])
            if gps_info[1] in ["S", "s"]:
                lat = -lat
            lng = _convert_to_deg(gps_info[4])
            if gps_info[3] in ["W", "w"]:
                lng = -lng
        taken_at = None
        if 29 in gps_info:  # GPSDateStamp
            date_str = gps_info[29]
            if date_str:
                try:
                    taken_at = datetime.strptime(date_str, "%Y:%m:%d")
                except Exception:
                    taken_at = None
        return lat, lng, taken_at.isoformat() if taken_at else None
    except Exception:
        return None, None, None


def save_route_photo(file: UploadFile, route_id: int, caption: str | None = None) -> RoutePhoto:
    """Save a photo for a route."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="File must be an image (jpg, png, webp)")

    # Ensure route exists - check in database
    query_check = "SELECT id FROM routes WHERE id = %s;"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query_check, (route_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Route not found")

    backend_dir = Path(__file__).parent.parent.parent.parent
    photos_dir = backend_dir / "static" / "route_photos"
    thumbs_dir = photos_dir / "thumbs"
    photos_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filenames
    stem = f"{uuid.uuid4()}"
    orig_ext = Path(file.filename).suffix.lower() or ".jpg"
    photo_filename = f"{stem}{orig_ext}"
    thumb_filename = f"{stem}_thumb.webp"

    try:
        content = file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file upload")

        image = Image.open(BytesIO(content))

        # Extract EXIF GPS/timestamp
        lat, lng, taken_at = _extract_exif_coords(image)

        # Resize to max 1600px on the longest side to save space
        max_side = 1600
        if max(image.size) > max_side:
            image.thumbnail((max_side, max_side), Image.LANCZOS)

        # Save original (converted to WebP for space)
        photo_path = photos_dir / f"{stem}.webp"
        image.save(photo_path, "WEBP", quality=90, method=6)

        # Create thumbnail (320px)
        thumb_image = image.copy()
        thumb_image.thumbnail((320, 320), Image.LANCZOS)
        thumb_path = thumbs_dir / thumb_filename
        thumb_image.save(thumb_path, "WEBP", quality=85, method=6)

        photo_url = f"/static/route_photos/{photo_path.name}"
        thumb_url = f"/static/route_photos/thumbs/{thumb_filename}"

        # Persist in DB
        query = """
            INSERT INTO route_photos (route_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, route_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude, created_at;
        """
        params = (
            route_id,
            photo_url,
            thumb_url,
            caption,
            taken_at,
            lat,
            lng,
        )
        with get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    conn.commit()
            except Exception as exc:
                conn.rollback()
                raise HTTPException(status_code=500, detail=f"Error saving photo: {str(exc)}") from exc

        return RoutePhoto(
            id=row[0],
            route_id=row[1],
            photo_url=row[2],
            thumbnail_url=row[3],
            caption=row[4],
            taken_at=row[5].isoformat() if row[5] else None,
            latitude=row[6],
            longitude=row[7],
            created_at=row[8].isoformat() if row[8] else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error processing photo: {str(exc)}") from exc


def list_route_photos(route_id: int) -> List[RoutePhoto]:
    """List photos for a route."""
    # Ensure route exists - check in database
    query_check = "SELECT id FROM routes WHERE id = %s;"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query_check, (route_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Route not found")
    query = """
        SELECT id, route_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude, created_at
        FROM route_photos
        WHERE route_id = %s
        ORDER BY created_at DESC;
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (route_id,))
                rows = cur.fetchall()
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Error querying route photos") from exc

    return [
        RoutePhoto(
            id=row[0],
            route_id=row[1],
            photo_url=row[2],
            thumbnail_url=row[3],
            caption=row[4],
            taken_at=row[5].isoformat() if row[5] else None,
            latitude=row[6],
            longitude=row[7],
            created_at=row[8].isoformat() if row[8] else None,
        )
        for row in rows
    ]


def reprocess_route_photo_gps(photo_id: int) -> RoutePhoto:
    """Re-process a photo to extract GPS coordinates from the file if missing."""
    # Get photo info from DB
    query_get = """
        SELECT id, route_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude, created_at
        FROM route_photos
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query_get, (photo_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Photo not found")
            
            # If already has GPS, return as-is
            if row[6] is not None and row[7] is not None:
                return RoutePhoto(
                    id=row[0],
                    route_id=row[1],
                    photo_url=row[2],
                    thumbnail_url=row[3],
                    caption=row[4],
                    taken_at=row[5].isoformat() if row[5] else None,
                    latitude=row[6],
                    longitude=row[7],
                    created_at=row[8].isoformat() if row[8] else None,
                )
            
            # Try to extract GPS from the file
            backend_dir = Path(__file__).parent.parent.parent.parent
            photo_path = backend_dir / row[2].lstrip("/")
            
            if not photo_path.exists():
                raise HTTPException(status_code=404, detail="Photo file not found")
            
            try:
                image = Image.open(photo_path)
                lat, lng, taken_at = _extract_exif_coords(image)
                
                if lat is None or lng is None:
                    raise HTTPException(status_code=400, detail="No GPS data found in photo EXIF")
                
                # Update database
                query_update = """
                    UPDATE route_photos
                    SET latitude = %s, longitude = %s, taken_at = COALESCE(taken_at, %s)
                    WHERE id = %s
                    RETURNING id, route_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude, created_at;
                """
                cur.execute(query_update, (lat, lng, taken_at, photo_id))
                updated_row = cur.fetchone()
                conn.commit()
                
                return RoutePhoto(
                    id=updated_row[0],
                    route_id=updated_row[1],
                    photo_url=updated_row[2],
                    thumbnail_url=updated_row[3],
                    caption=updated_row[4],
                    taken_at=updated_row[5].isoformat() if updated_row[5] else None,
                    latitude=updated_row[6],
                    longitude=updated_row[7],
                    created_at=updated_row[8].isoformat() if updated_row[8] else None,
                )
            except HTTPException:
                raise
            except Exception as exc:
                conn.rollback()
                raise HTTPException(status_code=500, detail=f"Error processing photo: {str(exc)}") from exc


def reprocess_route_photos_gps(route_id: int) -> List[RoutePhoto]:
    """Re-process all photos for a route to extract GPS coordinates if missing."""
    # Get all photos for the route
    photos = list_route_photos(route_id)
    results = []
    
    for photo in photos:
        # Only process photos without GPS
        if photo.latitude is None or photo.longitude is None:
            try:
                reprocessed = reprocess_route_photo_gps(photo.id)
                results.append(reprocessed)
            except HTTPException as e:
                # Skip photos that can't be processed (no GPS in EXIF, file missing, etc.)
                if e.status_code == 400:
                    # No GPS data - skip this photo
                    continue
                raise
    
    return results


def delete_route_photo(photo_id: int) -> dict:
    """Delete a route photo."""
    query = "DELETE FROM route_photos WHERE id = %s RETURNING id;"
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (photo_id,))
                row = cur.fetchone()
                conn.commit()
                if not row:
                    raise HTTPException(status_code=404, detail="Photo not found")
        except HTTPException:
            raise
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=500, detail="Error deleting photo") from exc

    return {"deleted_id": row[0], "message": "Photo deleted"}

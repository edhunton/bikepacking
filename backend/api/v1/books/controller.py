from typing import List
import uuid
from datetime import datetime
from pathlib import Path
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, ExifTags

from fastapi import HTTPException

from .db import get_connection
from .models import Book, UpdateBook, BookPhoto, CreateBookPhoto


def get_all_books() -> List[Book]:
    """
    Retrieve all books from the database.
    
    Returns:
        List of Book objects
        
    Raises:
        HTTPException: If database query fails
    """
    query = """
        SELECT id, title, author, published_at, isbn, cover_url, purchase_url
        FROM books
        ORDER BY id;
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        except Exception as exc:  # pragma: no cover - simple API surface
            raise HTTPException(status_code=500, detail="Error querying books") from exc

    return [
        Book(
            id=row[0],
            title=row[1],
            author=row[2],
            published_at=row[3],
            isbn=row[4] if len(row) > 4 else None,
            cover_url=row[5] if len(row) > 5 else None,
            purchase_url=row[6] if len(row) > 6 else None,
        )
        for row in rows
    ]


def get_book_by_id(book_id: int) -> Book:
    query = """
        SELECT id, title, author, published_at, isbn, cover_url, purchase_url
        FROM books
        WHERE id = %s;
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (book_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Book not found")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Error querying book") from exc

    return Book(
        id=row[0],
        title=row[1],
        author=row[2],
        published_at=row[3],
        isbn=row[4] if len(row) > 4 else None,
        cover_url=row[5] if len(row) > 5 else None,
        purchase_url=row[6] if len(row) > 6 else None,
    )


def update_book(book_id: int, data: UpdateBook) -> Book:
    existing = get_book_by_id(book_id)

    updates = []
    params = []
    if data.title is not None:
        updates.append("title = %s")
        params.append(data.title)
    if data.author is not None:
        updates.append("author = %s")
        params.append(data.author)
    if data.published_at is not None:
        updates.append("published_at = %s")
        params.append(data.published_at)
    if data.isbn is not None:
        updates.append("isbn = %s")
        params.append(data.isbn)
    if data.cover_url is not None:
        updates.append("cover_url = %s")
        params.append(data.cover_url)
    if data.purchase_url is not None:
        updates.append("purchase_url = %s")
        params.append(data.purchase_url)

    if not updates:
        return existing

    query = f"""
        UPDATE books
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, title, author, published_at, isbn, cover_url, purchase_url;
    """
    params.append(book_id)

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                conn.commit()
                if not row:
                    raise HTTPException(status_code=404, detail="Book not found")
        except HTTPException:
            raise
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=500, detail="Error updating book") from exc

    return Book(
        id=row[0],
        title=row[1],
        author=row[2],
        published_at=row[3],
        isbn=row[4],
        cover_url=row[5],
        purchase_url=row[6],
    )


# ---------- Book Photos ----------

def _extract_exif_coords(image: Image.Image):
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


def save_book_photo(file: UploadFile, book_id: int, caption: str | None = None) -> BookPhoto:
    # Validate input
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="File must be an image (jpg, png, webp)")

    # Ensure book exists
    get_book_by_id(book_id)

    backend_dir = Path(__file__).parent.parent.parent.parent
    photos_dir = backend_dir / "static" / "book_photos"
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

        photo_url = f"/static/book_photos/{photo_path.name}"
        thumb_url = f"/static/book_photos/thumbs/{thumb_filename}"

        # Persist in DB
        query = """
            INSERT INTO book_photos (book_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, book_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude, created_at;
        """
        params = (
            book_id,
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

        return BookPhoto(
            id=row[0],
            book_id=row[1],
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


def list_book_photos(book_id: int) -> List[BookPhoto]:
    # Ensure book exists
    get_book_by_id(book_id)
    query = """
        SELECT id, book_id, photo_url, thumbnail_url, caption, taken_at, latitude, longitude, created_at
        FROM book_photos
        WHERE book_id = %s
        ORDER BY created_at DESC;
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (book_id,))
                rows = cur.fetchall()
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Error querying book photos") from exc

    return [
        BookPhoto(
            id=row[0],
            book_id=row[1],
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


def delete_book_photo(photo_id: int) -> dict:
    query = "DELETE FROM book_photos WHERE id = %s RETURNING id;"
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

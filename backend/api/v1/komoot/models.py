from typing import List, Optional
from pydantic import BaseModel


class KomootTour(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    distance: Optional[float] = None  # in meters
    duration: Optional[int] = None  # in seconds
    elevation_gain: Optional[float] = None  # in meters
    elevation_loss: Optional[float] = None  # in meters
    difficulty: Optional[str] = None  # Can be a string or extracted from dict with 'grade' key
    surface: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    map_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    komoot_url: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[List[dict]] = None


class KomootCollection(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    item_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    thumbnail_url: Optional[str] = None
    komoot_url: Optional[str] = None
    items: Optional[List[dict]] = None  # Tours, highlights, or routes in the collection



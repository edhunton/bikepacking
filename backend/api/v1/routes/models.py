from typing import Optional
from pydantic import BaseModel


class Route(BaseModel):
    id: int
    title: str
    gpx_url: Optional[str] = None
    difficulty: Optional[str] = None
    country: Optional[str] = None
    county: Optional[str] = None
    distance: Optional[float] = None  # in kilometers
    ascent: Optional[int] = None  # in meters (elevation gain)
    descent: Optional[int] = None  # in meters (elevation loss)
    starting_station: Optional[str] = None
    ending_station: Optional[str] = None
    getting_there: Optional[str] = None
    bike_choice: Optional[str] = None
    guidebook_id: Optional[int] = None  # Foreign key to books table
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateRoute(BaseModel):
    title: str
    gpx_url: Optional[str] = None
    difficulty: Optional[str] = None
    country: Optional[str] = None
    county: Optional[str] = None
    distance: Optional[float] = None
    ascent: Optional[int] = None
    descent: Optional[int] = None
    starting_station: Optional[str] = None
    ending_station: Optional[str] = None
    getting_there: Optional[str] = None
    bike_choice: Optional[str] = None
    guidebook_id: Optional[int] = None


class UpdateRoute(BaseModel):
    title: Optional[str] = None
    gpx_url: Optional[str] = None
    difficulty: Optional[str] = None
    country: Optional[str] = None
    county: Optional[str] = None
    distance: Optional[float] = None
    ascent: Optional[int] = None
    descent: Optional[int] = None
    starting_station: Optional[str] = None
    ending_station: Optional[str] = None
    getting_there: Optional[str] = None
    bike_choice: Optional[str] = None
    guidebook_id: Optional[int] = None
    live: Optional[bool] = None  # Allow toggling live status

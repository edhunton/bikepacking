from typing import Optional, List
from pydantic import BaseModel


class Route(BaseModel):
    id: int
    title: str
    gpx_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
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
    min_time: Optional[float] = None  # Minimum time in days
    max_time: Optional[float] = None  # Maximum time in days
    off_road_distance: Optional[float] = None  # Off-road distance in kilometers
    off_road_percentage: Optional[float] = None  # Percentage of route that is off-road (0-100)
    grade: Optional[str] = None  # Grade: easy, moderate, difficult, hard, very hard
    description: Optional[str] = None  # Detailed description
    strava_activities: Optional[str] = None  # JSON array or comma-separated Strava activity IDs/URLs
    google_mymap_url: Optional[str] = None  # Link to Google MyMap
    komoot_collections: Optional[str] = None  # JSON array or comma-separated Komoot collection IDs/URLs
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateRoute(BaseModel):
    title: str
    gpx_url: Optional[str] = None
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
    min_time: Optional[float] = None
    max_time: Optional[float] = None
    off_road_distance: Optional[float] = None
    off_road_percentage: Optional[float] = None
    grade: Optional[str] = None
    description: Optional[str] = None
    strava_activities: Optional[str] = None
    google_mymap_url: Optional[str] = None
    komoot_collections: Optional[str] = None


class UpdateRoute(BaseModel):
    title: Optional[str] = None
    gpx_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
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
    min_time: Optional[float] = None
    max_time: Optional[float] = None
    off_road_distance: Optional[float] = None
    off_road_percentage: Optional[float] = None
    grade: Optional[str] = None
    description: Optional[str] = None
    strava_activities: Optional[str] = None
    google_mymap_url: Optional[str] = None
    komoot_collections: Optional[str] = None
    live: Optional[bool] = None  # Allow toggling live status


class RoutePhoto(BaseModel):
    id: int
    route_id: int
    photo_url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    taken_at: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[str] = None


class CreateRoutePhoto(BaseModel):
    route_id: int
    caption: Optional[str] = None

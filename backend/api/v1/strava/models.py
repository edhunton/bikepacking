from typing import Optional
from pydantic import BaseModel


class StravaActivity(BaseModel):
    id: int
    name: str
    type: str
    distance: float  # in meters
    moving_time: int  # in seconds
    elapsed_time: int  # in seconds
    total_elevation_gain: Optional[float] = None  # in meters
    start_date: str
    start_date_local: str
    timezone: str
    average_speed: Optional[float] = None  # in m/s
    max_speed: Optional[float] = None  # in m/s
    average_cadence: Optional[float] = None
    average_watts: Optional[float] = None
    weighted_average_watts: Optional[float] = None
    kilojoules: Optional[float] = None
    device_watts: Optional[bool] = None
    has_heartrate: Optional[bool] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    calories: Optional[int] = None
    map: Optional[dict] = None
    photos: Optional[dict] = None
    description: Optional[str] = None
    gear_id: Optional[str] = None
    gear: Optional[dict] = None



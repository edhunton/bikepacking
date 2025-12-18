from typing import List, Optional
from pydantic import BaseModel


class InstagramMedia(BaseModel):
    """Instagram media/post model."""
    id: str
    caption: Optional[str] = None
    media_type: str  # IMAGE, VIDEO, CAROUSEL_ALBUM
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    permalink: Optional[str] = None
    timestamp: Optional[str] = None
    username: Optional[str] = None
    like_count: Optional[int] = None
    comments_count: Optional[int] = None
    children: Optional[List["InstagramMedia"]] = None  # For carousel albums


class InstagramUser(BaseModel):
    """Instagram user model."""
    id: str
    username: str
    account_type: Optional[str] = None  # BUSINESS, CREATOR, PERSONAL
    media_count: Optional[int] = None


# Update forward reference
InstagramMedia.model_rebuild()



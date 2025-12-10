from typing import List, Optional

from fastapi import APIRouter, Query

from .controller import get_blog_posts as get_blog_posts_controller
from .models import BlogPost

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Lightweight endpoint to confirm the blog-posts router is live."""
    return {"status": "ok"}


@router.get("/", response_model=List[BlogPost])
def get_blog_posts(
    usernames: Optional[str] = Query(
        None, 
        description="Comma-separated list of Medium usernames (without @). If not provided, uses defaults."
    ),
    include_content: bool = Query(
        False,
        description="Include full post content (default: False, only excerpt)"
    )
) -> List[BlogPost]:
    """
    Fetch blog posts from Medium RSS feed(s).
    
    Medium RSS feed URL format: https://medium.com/feed/username
    
    Can fetch from multiple Medium accounts by providing comma-separated usernames.
    """
    return get_blog_posts_controller(usernames=usernames, include_content=include_content)

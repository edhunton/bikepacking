from typing import Optional
from pydantic import BaseModel


class BlogPost(BaseModel):
    title: str
    link: str
    published: str = ""
    author: str = "Unknown"
    excerpt: str = ""  # Allow empty excerpt
    content: Optional[str] = None
    thumbnail: Optional[str] = None



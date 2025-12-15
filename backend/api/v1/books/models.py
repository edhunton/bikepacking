from datetime import date
from pydantic import BaseModel


class Book(BaseModel):
    id: int
    title: str
    author: str
    published_at: date | None = None
    isbn: str | None = None
    cover_url: str | None = None
    purchase_url: str | None = None

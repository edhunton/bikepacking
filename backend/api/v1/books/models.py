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


class UpdateBook(BaseModel):
    title: str | None = None
    author: str | None = None
    published_at: date | None = None
    isbn: str | None = None
    cover_url: str | None = None
    purchase_url: str | None = None


class BookPhoto(BaseModel):
    id: int
    book_id: int
    photo_url: str
    thumbnail_url: str | None = None
    caption: str | None = None
    taken_at: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: str | None = None


class CreateBookPhoto(BaseModel):
    book_id: int
    caption: str | None = None

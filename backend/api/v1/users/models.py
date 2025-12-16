from enum import Enum
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRole(str, Enum):
    """User role enum - matches the database user_role enum."""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    id: int
    name: str  # Kept for backward compatibility (computed from first_name + last_name)
    first_name: str
    last_name: str
    age: Optional[int] = None
    email: EmailStr
    role: UserRole
    active: bool


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    age: Optional[int] = None
    email: EmailStr
    role: UserRole = UserRole.USER
    password: str


class UserInDB(User):
    password_hash: str
    # UserInDB inherits first_name and last_name from User


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


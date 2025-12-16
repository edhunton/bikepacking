from fastapi import APIRouter, Depends, HTTPException, status

from .controller import (
    create_user,
    get_user_by_email,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin_user,
)
from .models import User, CreateUser, LoginRequest, Token, UserRole


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: CreateUser, _: User = Depends(get_current_admin_user)) -> User:
    """Create a new user (admin only)."""
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return create_user(user)


@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
def signup(user: CreateUser) -> User:
    """Public signup endpoint - creates user with default role 'user'."""
    # Force role to 'user' for public signups
    user.role = UserRole.USER
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return create_user(user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest) -> Token:
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return Token(access_token=access_token)


@router.get("/me", response_model=User)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


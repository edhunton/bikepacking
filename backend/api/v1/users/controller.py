import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from .db import get_connection
from .models import User, CreateUser, UserInDB, UserRole

logger = logging.getLogger(__name__)


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Use bcrypt directly for password hashing
# We pre-hash passwords with SHA256 (produces 32 bytes) before bcrypt
# This avoids bcrypt's 72-byte limit entirely
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def _pre_hash_password(password: str) -> str:
    """
    Pre-hash password with SHA256 to produce a fixed 32-byte hash.
    This ensures the input to bcrypt is always exactly 32 bytes, well within the 72-byte limit.
    This approach completely avoids bcrypt's 72-byte limit issue.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    # Strip whitespace
    password = password.strip()
    if not password:
        raise ValueError("Password cannot be empty")
    # Hash with SHA256 to get a fixed 32-byte output (64 hex characters)
    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return sha256_hash


def get_password_hash(password: str) -> str:
    """
    Hash a password using SHA256 + bcrypt.
    First hash with SHA256 (produces 32 bytes), then hash that with bcrypt.
    This completely avoids bcrypt's 72-byte limit.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Pre-hash with SHA256 to get a fixed 32-byte string (64 hex characters)
    pre_hashed = _pre_hash_password(password)
    
    # Hash the SHA256 hash with bcrypt directly
    # The SHA256 hash is always 64 hex characters (32 bytes when encoded), well within bcrypt's 72-byte limit
    # Encode to bytes for bcrypt
    password_bytes = pre_hashed.encode("utf-8")
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string (bcrypt hash is already a string-like format)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    Pre-hash the plain password with SHA256, then verify against the bcrypt hash.
    
    For backward compatibility: if the new method fails, try the old method
    (direct password verification) in case the hash was created with the old system.
    """
    if not plain_password:
        return False
    
    # Try new method: pre-hash with SHA256, then verify with bcrypt directly
    try:
        pre_hashed = _pre_hash_password(plain_password)
        password_bytes = pre_hashed.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        if bcrypt.checkpw(password_bytes, hash_bytes):
            return True
    except (ValueError, Exception):
        # If pre-hashing fails, fall through to old method
        pass
    
    # Fallback: try old method (direct password verification) for backward compatibility
    # This handles passwords hashed with the old system before we switched to SHA256 pre-hashing
    # Note: This will fail for passwords > 72 bytes, but that's expected
    try:
        # Strip and truncate to 72 bytes for old hashes
        safe_password = plain_password.strip()
        encoded = safe_password.encode("utf-8")
        if len(encoded) > 72:
            safe_password = encoded[:72].decode("utf-8", errors="ignore")
        password_bytes = safe_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, Exception):
        # If both methods fail, password is incorrect
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(email: str) -> Optional[UserInDB]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''), 
                       COALESCE(first_name, ''), COALESCE(last_name, ''), age, email, role, active, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return None
            # Compute name from first_name + last_name, or fallback to old name field
            full_name = (row[2] or "").strip() + " " + (row[3] or "").strip()
            full_name = full_name.strip() or row[1]  # Fallback to old name if first/last are empty
            # Convert role string to UserRole enum
            role = UserRole(row[6]) if row[6] else UserRole.USER
            return UserInDB(
                id=row[0],
                name=full_name,
                first_name=row[2] or "",
                last_name=row[3] or "",
                age=row[4],
                email=row[5],
                role=role,
                active=row[7],
                password_hash=row[8],
            )


def create_user(user: CreateUser) -> User:
    password_hash = get_password_hash(user.password)
    # Compute full name for backward compatibility
    full_name = f"{user.first_name} {user.last_name}".strip()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, first_name, last_name, age, email, role, active, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, first_name, last_name, age, email, role, active
                """,
                (full_name, user.first_name, user.last_name, user.age, user.email, user.role.value, True, password_hash),
            )
            row = cur.fetchone()
            conn.commit()
        # Convert role string to UserRole enum
        role = UserRole(row[6]) if row[6] else UserRole.USER
        return User(
            id=row[0],
            name=full_name,
            first_name=row[2] or user.first_name,
            last_name=row[3] or user.last_name,
            age=row[4],
            email=row[5],
            role=role,
            active=row[7],
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning(f"JWT token missing 'sub' claim. Token: {token[:50]}...")
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}. Token: {token[:50] if token else 'None'}...")
        raise credentials_exception
    except jwt.PyJWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise credentials_exception

    user = get_user_by_email(email=email)
    if user is None:
        logger.warning(f"User not found for email from token: {email}")
        raise credentials_exception
    if not user.active:
        logger.warning(f"User is inactive: {email}")
        raise credentials_exception
    return user


async def get_current_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


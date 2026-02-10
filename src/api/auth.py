"""
Authentication - JWT token-based authentication with bcrypt password hashing.

Features:
- Login endpoint (username + password → JWT tokens)
- Token validation and user extraction
- Password hashing with bcrypt
- Access token (15 min) + Refresh token (7 days)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import User

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_TO_RANDOM_64_CHAR_STRING")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data (should include 'sub' with username)
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token (longer expiry).

    Args:
        data: Payload data (should include 'sub' with username)

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[User]:
    """
    Authenticate user by username and password.

    Args:
        db: Database session
        username: Username
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    # Look up user by username
    result = await db.execute(select(User).filter_by(username=username))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Login attempt for non-existent user: {username}")
        return None

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {username}")
        return None

    # Check if user is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        logger.warning(f"Login attempt for locked user: {username}")
        return None

    # Verify password
    if not verify_password(password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {username}")

        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts (30 min lockout)
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            logger.warning(f"User locked due to failed attempts: {username}")

        await db.commit()
        return None

    # Successful login - reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    await db.commit()

    logger.info(f"Successful login: {username}")
    return user


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify JWT token and extract username.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Username if token valid, None otherwise

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type (expected {token_type})",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return username

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get user by username.

    Args:
        db: Database session
        username: Username

    Returns:
        User object or None
    """
    result = await db.execute(select(User).filter_by(username=username))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str = "officer",
    **kwargs
) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        username: Username
        email: Email address
        password: Plain text password (will be hashed)
        full_name: Full name
        role: User role (officer, supervisor, admin)
        **kwargs: Additional user fields

    Returns:
        Created User object
    """
    # Check if username already exists
    existing = await get_user_by_username(db, username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create user with hashed password
    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        role=role,
        **kwargs
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User created: {username} (role: {role})")
    return user

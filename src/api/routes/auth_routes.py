"""
Authentication Routes - Login, token refresh, logout.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_user_by_username,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models import User
from src.api.schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.

    Returns JWT access token (15 min) and refresh token (7 days).
    """
    user = await authenticate_user(db, request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Accepts a valid refresh token and returns a new access token.
    """
    # Verify refresh token
    username = verify_token(request.refresh_token, token_type="refresh")

    # Get user
    user = await get_user_by_username(db, username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token or user inactive"
        )

    # Create new access token
    access_token = create_access_token(data={"sub": user.username})

    logger.info(f"Access token refreshed for user: {user.username}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # Return same refresh token
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get information about the currently authenticated user.

    Requires valid access token in Authorization header.
    """
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.

    Note: Since we use JWTs (stateless), actual logout is handled client-side
    by discarding the tokens. This endpoint is mainly for audit logging.
    """
    logger.info(f"User logged out: {current_user.username}")

    return {"message": "Successfully logged out"}

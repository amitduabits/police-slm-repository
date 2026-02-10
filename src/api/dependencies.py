"""
Dependencies - FastAPI dependency injection for auth, database, etc.

Provides:
- get_current_user: Extract authenticated user from JWT token
- require_role: Check user has required role
- get_rag_pipeline: Get RAG pipeline instance
"""

import logging
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import verify_token, get_user_by_username
from src.api.database import get_db
from src.api.models import User

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get currently authenticated user from JWT token.

    Usage:
        @app.get("/protected")
        async def protected_endpoint(user: User = Depends(get_current_user)):
            return {"username": user.username}

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token invalid or user not found
    """
    # Verify token and extract username
    username = verify_token(token, token_type="access")

    # Get user from database
    user = await get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get current active user.
    Alias for get_current_user with explicit active check.

    Args:
        user: User from get_current_user

    Returns:
        Active user object
    """
    return user


def require_role(*allowed_roles: str):
    """
    Dependency factory to check user has one of the allowed roles.

    Usage:
        @app.get("/admin/users")
        async def list_users(user: User = Depends(require_role("admin", "supervisor"))):
            ...

    Args:
        *allowed_roles: Roles allowed to access the endpoint

    Returns:
        Dependency function
    """
    async def check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            logger.warning(
                f"User {user.username} (role: {user.role}) attempted to access "
                f"endpoint requiring roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {' or '.join(allowed_roles)}"
            )
        return user

    return check_role


def get_rag_pipeline():
    """
    Dependency to get RAG pipeline instance.

    Usage:
        @app.post("/sop/suggest")
        async def suggest_sop(
            request: SOPRequest,
            rag = Depends(get_rag_pipeline)
        ):
            result = rag.query(request.fir_details, use_case="sop")
            ...

    Returns:
        RAG pipeline instance
    """
    from src.retrieval.rag_pipeline import create_rag_pipeline

    # Cache the pipeline instance (create once, reuse)
    if not hasattr(get_rag_pipeline, "_pipeline"):
        logger.info("Initializing RAG pipeline...")
        get_rag_pipeline._pipeline = create_rag_pipeline()
        logger.info("RAG pipeline ready")

    return get_rag_pipeline._pipeline


def get_section_normalizer():
    """
    Dependency to get section normalizer instance.

    Returns:
        SectionNormalizer instance
    """
    from src.ingestion.section_normalizer import SectionNormalizer

    if not hasattr(get_section_normalizer, "_normalizer"):
        logger.info("Initializing section normalizer...")
        get_section_normalizer._normalizer = SectionNormalizer()
        logger.info("Section normalizer ready")

    return get_section_normalizer._normalizer

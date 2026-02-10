"""
Database Configuration - Supports both PostgreSQL and SQLite.

For development: SQLite (no Docker needed)
For production: PostgreSQL
"""

import os
import logging
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Base class for all ORM models
Base = declarative_base()

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/gujpol.db")

# Convert to async driver
if DATABASE_URL.startswith("postgresql://"):
    # Use asyncpg for PostgreSQL
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite://"):
    # Use aiosqlite for SQLite
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

logger.info(f"Database: {ASYNC_DATABASE_URL.split('@')[0].split('//')[0]}")  # Hide credentials

# Create async engine
if "sqlite" in ASYNC_DATABASE_URL:
    # SQLite-specific configuration
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=0,
    )

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database: create tables and default data.

    For SQLite: Creates tables directly from models
    For PostgreSQL: Assumes schema already applied via init-db.sql
    """
    from src.api.models import User  # Import here to avoid circular dependency

    # Ensure data directory exists for SQLite
    if "sqlite" in ASYNC_DATABASE_URL:
        db_path = Path(ASYNC_DATABASE_URL.replace("sqlite+aiosqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created")

    # Create default admin user if not exists
    async with async_session_maker() as session:
        try:
            from sqlalchemy import select

            result = await session.execute(select(User).filter_by(username="admin"))
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                from passlib.context import CryptContext

                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

                admin_user = User(
                    username="admin",
                    email="admin@gujpol.gov.in",
                    password_hash=pwd_context.hash("changeme"),
                    full_name="System Administrator",
                    role="admin",
                    district="Gandhinagar",
                    is_active=True,
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Default admin user created (username: admin, password: changeme)")
            else:
                logger.info("Admin user already exists")

        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
            await session.rollback()


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")


# Enable foreign keys for SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    if "sqlite" in ASYNC_DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

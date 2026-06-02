"""Database connection and session handling (async SQLAlchemy)."""
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class all database models inherit from."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session to a request, then close it."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables. Called once when the server starts."""
    # Import models so they are registered on Base before create_all.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight migration: add columns introduced in Step 6 to an
        # already-existing Postgres table (create_all won't alter existing
        # tables). Idempotent; legacy rows default to "done". SQLite tables are
        # created fresh by create_all above, so this only runs on Postgres.
        if conn.dialect.name == "postgresql":
            await conn.execute(
                text("ALTER TABLE scans ADD COLUMN IF NOT EXISTS status "
                     "VARCHAR NOT NULL DEFAULT 'done'")
            )
            await conn.execute(
                text("ALTER TABLE scans ADD COLUMN IF NOT EXISTS error VARCHAR")
            )

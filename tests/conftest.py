"""Shared test setup: a fresh, isolated database per test via an in-memory SQLite."""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.deps import get_predictor
from app.main import app
from app.routers import scans as scans_router


async def fake_predict(image_bytes: bytes) -> tuple[str, float]:
    """Offline stand-in for the real model, so tests are fast and deterministic."""
    return ("Melanocytic Nevi", 0.93)


@pytest_asyncio.fixture
async def client():
    """An HTTP client wired to the app, backed by a clean throwaway database."""
    # In-memory SQLite, shared across the test via a single pooled connection.
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_predictor] = lambda: fake_predict

    # The background task opens its own session via AsyncSessionLocal — point
    # that at the test database too, then restore it afterwards.
    original_session_factory = scans_router.AsyncSessionLocal
    scans_router.AsyncSessionLocal = test_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    scans_router.AsyncSessionLocal = original_session_factory
    app.dependency_overrides.clear()
    await engine.dispose()

"""
Skin Triage API — entry point.

Step 2 (current): the server now supports user accounts — sign up, log in,
and a 'who am I' check — backed by a database. Saved scan history and the
model integration are added in later steps.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, scans


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables when the server starts."""
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Backend for the skin-disease triage app: accounts + saved scan history.",
    lifespan=lifespan,
)

# Allow a browser frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened to the real frontend origin before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scans.router)


@app.get("/")
def root():
    """Friendly landing response so visitors know the API is alive."""
    return {"name": settings.app_name, "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    """Health check used by tests, Docker, and the deploy platform."""
    return {"status": "healthy", "environment": settings.environment}

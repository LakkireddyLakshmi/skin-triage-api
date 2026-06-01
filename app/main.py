"""
Skin Triage API — entry point.

Step 1 (current): a minimal, healthy server with a versioned API and a
/health check. Accounts, database, and model integration are added in later
steps. The point of this step is a solid, tested, deployable foundation.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend for the skin-disease triage app: accounts + saved scan history.",
)

# Allow a browser frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened to the real frontend origin before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Friendly landing response so visitors know the API is alive."""
    return {"name": settings.app_name, "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    """Health check used by tests, Docker, and the deploy platform."""
    return {"status": "healthy", "environment": settings.environment}

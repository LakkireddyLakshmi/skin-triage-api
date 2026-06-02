"""Request/response shapes (what the API accepts and returns)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Body for signing up."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Body for logging in."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Public view of a user (never includes the password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    """The login token handed back after a successful login."""

    access_token: str
    token_type: str = "bearer"


class ScanRead(BaseModel):
    """A saved scan as returned to the user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str  # "processing" | "done" | "failed"
    predicted_label: str
    confidence: float
    error: str | None = None
    created_at: datetime

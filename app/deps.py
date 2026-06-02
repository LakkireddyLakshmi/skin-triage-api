"""Shared request dependencies, e.g. 'who is the logged-in user?'."""
from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app import predictor
from app.database import get_db
from app.models import User
from app.security import decode_access_token

# Type of a prediction function: bytes -> (label, confidence).
Predictor = Callable[[bytes], Awaitable[tuple[str, float]]]


def get_predictor() -> Predictor:
    """The function that turns an image into a prediction.

    Provided as a dependency so tests can swap in a fast offline fake while
    production uses the real Hugging Face model.
    """
    return predictor.predict

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the user from their login token, or reject the request."""
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise invalid

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise invalid

    user = await db.get(User, int(user_id))
    if user is None:
        raise invalid
    return user

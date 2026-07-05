"""Profile API models — a user's public username identity."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Profile(BaseModel):
    """A user's public profile as returned to clients."""

    id: UUID
    username: str
    created_at: datetime
    updated_at: datetime


class Me(BaseModel):
    """The caller's own view of themselves: their username (null until claimed)
    and their email — the ONLY place an email is ever returned, and only to its
    owner."""

    user_id: UUID
    email: str | None
    username: str | None


class UsernameClaim(BaseModel):
    """Request body to set/change the caller's username."""

    username: str = Field(min_length=1, max_length=40)


class UsernameCheck(BaseModel):
    """Availability response for a candidate username."""

    available: bool
    reason: str | None = None

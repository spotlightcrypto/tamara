"""Company API models.

Companies are a shared/global cache (not per-user). Bare-bones for now: identity
plus placeholders for profile/fundamentals that a later hydrate step will fill.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyAttach(BaseModel):
    """What a client sends to attach a company to a narrative.

    Only a ticker is required; `name` is optional (defaults to the ticker until
    a later hydrate step fetches the real name).
    """

    ticker: str = Field(min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=200)


class Company(BaseModel):
    """A company as returned to the client."""

    id: UUID
    ticker: str
    name: str
    exchange: str | None
    sector: str | None
    profile: dict[str, Any] | None
    fundamentals: dict[str, Any] | None
    last_hydrated_at: datetime | None
    created_at: datetime
    updated_at: datetime

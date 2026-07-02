"""Source API models — external links a narrative is grounded in.

When the intake kernel is a link (or contains links), each is captured as a
source so the finished narrative can show where it came from, presented as a
nicely-named external link.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Source(BaseModel):
    """A source as returned to the client."""

    id: UUID
    narrative_id: UUID
    url: str
    title: str  # short "few words" display name (falls back to the hostname)
    created_at: datetime

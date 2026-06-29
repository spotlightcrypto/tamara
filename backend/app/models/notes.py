"""Note API models — a user's free-text annotations on a narrative."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """What a client sends to add a note to a narrative."""

    body: str = Field(min_length=1, max_length=5000)


class NoteUpdate(BaseModel):
    """A partial edit to a note."""

    body: str | None = Field(default=None, min_length=1, max_length=5000)


class Note(BaseModel):
    """A note as returned to the client."""

    id: UUID
    narrative_id: UUID
    body: str
    created_at: datetime
    updated_at: datetime

"""Narrative API models.

These are NOT database rows — they're the typed shapes that cross the API
boundary. We use a *different* model for each job so the client can never set
server-owned fields (`id`, `user_id`, timestamps):

    NarrativeCreate  -> request body for POST /narratives
    NarrativeUpdate  -> request body for PATCH /narratives/{id} (partial edit)
    Narrative        -> the response we return (incl. server-set fields)
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.companies import Company


class NarrativeCreate(BaseModel):
    """What a client may send to create a narrative."""

    # Field(...) lets us attach validation rules. A title must be present and
    # non-empty (min_length=1) and reasonably short (max_length=200).
    title: str = Field(min_length=1, max_length=200)

    # Optional with a default: if the client omits `thesis`, it becomes "".
    thesis: str = ""


class NarrativeUpdate(BaseModel):
    """What a client may send to edit a narrative — a partial update.

    Every field is Optional (`... | None`) and defaults to None. A value of
    None means "the client didn't supply this field, so leave it unchanged".
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    thesis: str | None = None
    # All narratives start active; the owner can flip this to retire one.
    is_active: bool | None = None


class Narrative(BaseModel):
    """What the API returns to the client.

    Note the richer types: `id` is a real UUID and the timestamps are real
    datetimes. Pydantic validates/coerces incoming values (e.g. a UUID string
    from the database) into these types, and serializes them back to JSON in
    standard formats on the way out.
    """

    id: UUID
    title: str
    thesis: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NarrativeSummary(Narrative):
    """A narrative plus its attached companies, hydrated server-side in ONE query.

    List views (home, profile, a company's narratives) render a title and its
    ticker chips. Embedding the companies here lets the API answer with a single
    round-trip instead of the client firing an extra request per narrative.
    """

    companies: list[Company] = Field(default_factory=list)

"""Narrative item API models (bull / bear / catalyst / risk points)."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ItemKind(str, Enum):
    """The four sections a narrative item can belong to.

    Subclassing `str` means it serializes to its plain value ("bull", ...) in
    JSON, and Pydantic validates incoming values against these members — an
    unknown kind is rejected automatically (422).
    """

    bull = "bull"
    bear = "bear"
    catalyst = "catalyst"
    risk = "risk"


class ItemCreate(BaseModel):
    """What a client sends to add a point to a section.

    `position` is intentionally absent — the server appends new items to the end
    of their section (the client doesn't pick the order on create).
    """

    kind: ItemKind
    body: str = Field(min_length=1, max_length=1000)
    event_date: date | None = None  # only used by catalysts


class ItemUpdate(BaseModel):
    """A partial edit. `kind` may change too — that moves the item to another
    section. All fields optional (PATCH semantics)."""

    kind: ItemKind | None = None
    body: str | None = Field(default=None, min_length=1, max_length=1000)
    event_date: date | None = None


class ItemMove(BaseModel):
    """Body for reordering an item within its section."""

    position: int = Field(ge=0)


class Item(BaseModel):
    """A narrative item as returned to the client."""

    id: UUID
    narrative_id: UUID
    kind: ItemKind
    body: str
    event_date: date | None
    position: int
    created_at: datetime
    updated_at: datetime

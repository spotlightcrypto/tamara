"""Company API models.

Companies are a shared/global cache (not per-user). A company's identity is its
exchange-qualified ticker — the same symbol can trade on different exchanges, so
"CRWV" alone is ambiguous; "CRWV:NASDAQ" is not. We store `ticker` and `exchange`
separately and expose a derived `symbol` for display.

Bare-bones for now: identity + placeholders for profile/fundamentals that a later
hydrate step will fill.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, model_validator


class CompanyAttach(BaseModel):
    """What a client sends to attach a company to a narrative.

    An exchange is REQUIRED — a ticker is ambiguous without it. Provide it either
    as an exchange-qualified ticker ("CRWV:NASDAQ") or via the `exchange` field
    ("CRWV" + exchange="NASDAQ"). `name` is optional (defaults to the ticker).
    """

    ticker: str = Field(min_length=1, max_length=30)
    exchange: str | None = Field(default=None, max_length=20)
    name: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _require_exchange(self) -> "CompanyAttach":
        qualified = ":" in self.ticker and self.ticker.split(":", 1)[1].strip() != ""
        provided = bool(self.exchange and self.exchange.strip())
        if not (qualified or provided):
            raise ValueError(
                "exchange is required — use an exchange-qualified ticker like "
                "'CRWV:NASDAQ', or provide the `exchange` field"
            )
        return self


class Company(BaseModel):
    """A company as returned to the client."""

    id: UUID
    ticker: str
    exchange: str
    name: str
    sector: str | None
    profile: dict[str, Any] | None
    fundamentals: dict[str, Any] | None
    last_hydrated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def symbol(self) -> str:
        """Exchange-qualified display symbol, e.g. "CRWV:NASDAQ"."""
        return f"{self.ticker}:{self.exchange}"

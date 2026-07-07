"""Company API models.

Companies are a shared/global cache (not per-user). A company's identity is
(ticker, MIC) — the same ticker trades on different exchanges, so "CRWV" alone is
ambiguous and even "CRWV:NASDAQ" relies on a friendly name that varies by source.
The MIC (ISO 10383, e.g. XNAS) is the canonical, international key. We store the
MIC alongside the friendly `exchange` name and expose:
  - `symbol`: friendly display, "CRWV:NASDAQ"
  - `slug`:   canonical URL identity, "crwv:xnas" (ticker:mic, lowercased)

`currency`/`country`/`tier` come from the exchange registry (see app.exchanges);
`tier` drives price coverage (1 US, 2 major-developed via Yahoo, 3 narrative-only).

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
    exchange: str  # friendly display name ("NASDAQ")
    mic: str  # ISO 10383 canonical code ("XNAS") — the identity key
    currency: str | None
    country: str | None
    tier: int | None  # 1 US, 2 major-developed (priced via Yahoo), 3 narrative-only
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
        """Friendly exchange-qualified symbol for display, e.g. "CRWV:NASDAQ"."""
        return f"{self.ticker}:{self.exchange}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def slug(self) -> str:
        """Canonical URL identity: ticker:mic, lowercased, e.g. "crwv:xnas".
        Unambiguous across exchanges and stable regardless of naming source."""
        return f"{self.ticker}:{self.mic}".lower()

"""Search API models.

Two shapes:
  - `SearchResults`: what a local search returns — the caller's own narratives and
    globally-known companies matching the query.
  - `ResolvedListing`: an equity we found via the external symbol resolver but do
    NOT have in our DB yet. It has no `id` (nothing persisted); it carries just
    enough to render a chip and start the first narrative for it. Shaped to line
    up with `Company` (same `symbol`/`slug` derivation) so the frontend can treat
    the two nearly interchangeably.
"""

from pydantic import BaseModel, computed_field

from app.models.companies import Company
from app.models.narratives import NarrativeSummary


class ResolvedListing(BaseModel):
    """An external symbol-search hit, not (yet) persisted as a company."""

    ticker: str
    mic: str
    exchange: str  # friendly display name
    name: str
    currency: str | None
    tier: int | None
    has_price: bool  # do we have a free price source for this exchange yet?

    @computed_field  # type: ignore[prop-decorator]
    @property
    def symbol(self) -> str:
        return f"{self.ticker}:{self.exchange}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def slug(self) -> str:
        return f"{self.ticker}:{self.mic}".lower()


class SearchResults(BaseModel):
    """Combined local search: the caller's narratives + known companies."""

    narratives: list[NarrativeSummary]
    companies: list[Company]

"""Price API models."""

from datetime import date

from pydantic import BaseModel


class PricePerformance(BaseModel):
    """A ticker's percentage price performance over standard windows.

    `performance` maps a window label to a percent change, e.g.
    {"1D": -1.2, "1W": 3.4, "1M": 8.0, "3M": -5.1, "6M": 12.3, "1Y": 40.7}.
    A window is omitted when we don't have enough history to compute it. "1H"
    (and truly-live "1D") need an intraday feed and land once we enable it.
    """

    ticker: str
    as_of: date | None  # date of the latest bar the numbers are computed from
    performance: dict[str, float]

    # Optional "since a reference date" (e.g. when a narrative was created): the
    # close on/before that date, and the % change from then to `as_of`.
    since_date: date | None = None
    since_close: float | None = None
    since_change: float | None = None

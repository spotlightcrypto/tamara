"""Market-data provider (prices).

Provider-agnostic seam, like the LLM gateway: services call `grouped_daily()` and
never touch a vendor SDK. Today it's backed by Polygon.io's "Grouped Daily Bars"
endpoint, which returns EVERY US ticker's daily bar in a SINGLE request — the
bulk pattern that lets us scale to thousands of tickers on cheap/free plans.

Swapping to another bulk provider (EODHD, FMP, …) later is a new implementation
behind this same function, not a change to callers.
"""

from datetime import date

import httpx

from app.config import settings

_POLYGON_BASE = "https://api.polygon.io"
_TIMEOUT = 30.0


class PricesError(Exception):
    """A price fetch failed (network, auth, rate limit, bad response)."""


def grouped_daily(day: date) -> dict[str, float]:
    """Return {ticker: close} for every US stock on `day` in one API call.

    An empty dict means a non-trading day (weekend/holiday) or data not yet
    published. Tickers are bare US symbols (e.g. "AAPL"). Closes are adjusted.
    """
    if not settings.polygon_api_key:
        raise PricesError("POLYGON_API_KEY is not configured")

    url = f"{_POLYGON_BASE}/v2/aggs/grouped/locale/us/market/stocks/{day.isoformat()}"
    params = {"adjusted": "true", "apiKey": settings.polygon_api_key}
    try:
        resp = httpx.get(url, params=params, timeout=_TIMEOUT)
    except httpx.HTTPError as exc:
        raise PricesError(f"request failed: {exc}") from exc

    if resp.status_code == 429:
        raise PricesError("rate limited (429) — slow down or upgrade the plan")
    if resp.status_code != 200:
        raise PricesError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    # Grouped Daily response: {"results": [{"T": ticker, "c": close, ...}, ...]}.
    results = resp.json().get("results") or []
    out: dict[str, float] = {}
    for row in results:
        ticker, close = row.get("T"), row.get("c")
        if ticker and close is not None:
            out[ticker] = float(close)
    return out

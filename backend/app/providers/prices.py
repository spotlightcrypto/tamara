"""Market-data provider (prices).

Provider-agnostic seam, like the LLM gateway: services call `grouped_daily()` and
never touch a vendor SDK. Today it's backed by Polygon.io's "Grouped Daily Bars"
endpoint, which returns EVERY US ticker's daily bar in a SINGLE request — the
bulk pattern that lets us scale to thousands of tickers on cheap/free plans.

Swapping to another bulk provider (EODHD, FMP, …) later is a new implementation
behind this same function, not a change to callers.
"""

from datetime import date, datetime, timezone

import httpx

from app.config import settings

_POLYGON_BASE = "https://api.polygon.io"
_YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
_UA = {"User-Agent": "Mozilla/5.0 (Tamara)"}
_TIMEOUT = 30.0


class PricesError(Exception):
    """A price fetch failed (network, auth, rate limit, bad response)."""


# --- PROTOTYPE (keyless): per-ticker history from Yahoo -----------------------
#
# The Yahoo public chart endpoint (what `yfinance` wraps) needs no key, so we can
# prove the whole pipeline end-to-end now. It is PER-TICKER, so it does NOT scale
# to thousands of tickers — it's fine for our current handful of company tickers.
#
# TODO(prices): add POLYGON_API_KEY and switch the ingest to grouped_daily()
# below — the bulk, scalable production path — then confirm the full integration
# (backfill + daily cron) against real Polygon data. Until then we prototype here.

def daily_history(ticker: str, rng: str = "1y") -> list[tuple[date, float]]:
    """Daily (date, adjusted-close) for ONE ticker from Yahoo's chart endpoint.
    Empty list if the ticker is unknown or returns no data.

    `ticker` is the CANONICAL symbol (matches companies.ticker and Polygon's
    format, e.g. "BRK.B"). Yahoo uses a hyphen for class shares, so we translate
    only for the request URL — the caller still stores under the canonical
    symbol, keeping daily_bars keyed identically to the future Polygon path.
    """
    yahoo_symbol = ticker.replace(".", "-")
    url = f"{_YAHOO_CHART}/{yahoo_symbol}"
    params = {"range": rng, "interval": "1d"}
    try:
        resp = httpx.get(url, params=params, headers=_UA, timeout=_TIMEOUT)
    except httpx.HTTPError as exc:
        raise PricesError(f"request failed: {exc}") from exc
    if resp.status_code != 200:
        raise PricesError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    result = (resp.json().get("chart") or {}).get("result") or []
    if not result:
        return []
    r = result[0]
    timestamps = r.get("timestamp") or []
    indicators = r.get("indicators") or {}
    # Prefer adjusted close (splits/dividends) to match the production path.
    adj = (indicators.get("adjclose") or [{}])[0].get("adjclose")
    closes = adj if adj else (indicators.get("quote") or [{}])[0].get("close") or []

    out: list[tuple[date, float]] = []
    for ts, close in zip(timestamps, closes):
        if close is not None:
            out.append((datetime.fromtimestamp(ts, tz=timezone.utc).date(), float(close)))
    return out


# --- PRODUCTION (Polygon bulk): the whole market in one call ------------------

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

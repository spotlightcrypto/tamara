"""Business logic for prices.

Two halves:
  - INGEST: pull the whole market's daily bars in bulk and cache them in
    `daily_bars` (one API call per trading day, regardless of ticker count).
  - READ: compute a ticker's percentage performance over standard windows from
    the cached bars — a fast local read, no API call.

Intraday windows (1H, live 1D) need a delayed snapshot feed (paid) and are left
as a seam; today we compute the daily windows (1D/1W/1M/3M/6M/1Y).
"""

import time
from datetime import date, timedelta

from supabase import Client

from app.models import PricePerformance
from app.providers import prices as prices_provider

# Window label -> calendar-day lookback. We find the most recent bar at least
# that old (handles weekends/holidays: "on or before" the cutoff date).
_WINDOWS: list[tuple[str, int]] = [
    ("1W", 7),
    ("1M", 30),
    ("3M", 91),
    ("6M", 182),
    ("1Y", 365),
]

_UPSERT_CHUNK = 1000  # rows per upsert (the market is ~10k+ tickers)


def ingest_day(db: Client, day: date) -> int:
    """Fetch and cache every ticker's bar for one trading day. Returns the number
    of bars written (0 on a non-trading day). Idempotent — re-running overwrites."""
    bars = prices_provider.grouped_daily(day)
    if not bars:
        return 0
    rows = [
        {"ticker": ticker, "date": day.isoformat(), "close": close}
        for ticker, close in bars.items()
    ]
    for i in range(0, len(rows), _UPSERT_CHUNK):
        db.table("daily_bars").upsert(
            rows[i : i + _UPSERT_CHUNK], on_conflict="ticker,date"
        ).execute()
    return len(rows)


def ingest_ticker(db: Client, ticker: str, rng: str = "2y") -> int:
    """PROTOTYPE (keyless): cache one ticker's daily history from Yahoo. Returns
    the number of bars written. See providers/prices.py for the Polygon TODO."""
    bars = prices_provider.daily_history(ticker, rng)
    if not bars:
        return 0
    rows = [
        {"ticker": ticker, "date": bar_date.isoformat(), "close": close}
        for bar_date, close in bars
    ]
    for i in range(0, len(rows), _UPSERT_CHUNK):
        db.table("daily_bars").upsert(
            rows[i : i + _UPSERT_CHUNK], on_conflict="ticker,date"
        ).execute()
    return len(rows)


def ingest_watchlist(db: Client, rng: str = "2y") -> dict:
    """PROTOTYPE: cache history for every ticker that appears in a narrative
    (the companies table), one Yahoo call per ticker. Fine for our handful of
    tickers; the production path bulk-ingests the whole market via grouped_daily."""
    companies = db.table("companies").select("ticker").execute().data
    tickers = sorted({c["ticker"] for c in companies})
    ok = 0
    total = 0
    for ticker in tickers:
        try:
            written = ingest_ticker(db, ticker, rng)
        except Exception:
            continue  # skip a bad ticker rather than fail the whole run
        if written:
            ok += 1
            total += written
    return {"tickers": len(tickers), "ingested": ok, "bars": total}


def backfill(db: Client, days: int = 365, throttle_seconds: float = 0.0) -> dict:
    """Seed history by ingesting each of the last `days` calendar days (skipping
    weekends). `throttle_seconds` paces calls for rate-limited plans (Polygon
    free = 5/min, so ~13s). Long-running — run out-of-band, not in a request."""
    today = date.today()
    trading_days = 0
    total_bars = 0
    for i in range(1, days + 1):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:  # 5=Sat, 6=Sun
            continue
        written = ingest_day(db, day)
        if written:
            trading_days += 1
            total_bars += written
        if throttle_seconds:
            time.sleep(throttle_seconds)
    return {"trading_days": trading_days, "total_bars": total_bars}


def _pct(latest: float, ref: float) -> float:
    return round((latest - ref) / ref * 100, 2)


def performance(db: Client, ticker: str) -> PricePerformance:
    """Compute a ticker's percentage performance over the daily windows from the
    cached bars. Windows without enough history are omitted."""
    response = (
        db.table("daily_bars")
        .select("date,close")
        .eq("ticker", ticker)
        .order("date", desc=True)
        .limit(400)  # ~1.5 trading years — enough for the 1Y window
        .execute()
    )
    rows = response.data
    if not rows:
        return PricePerformance(ticker=ticker, as_of=None, performance={})

    # Newest first (date desc).
    bars = [(date.fromisoformat(r["date"]), float(r["close"])) for r in rows]
    latest_date, latest_close = bars[0]

    def ref_close(lookback_days: int) -> float | None:
        cutoff = latest_date - timedelta(days=lookback_days)
        for bar_date, bar_close in bars:  # desc -> first bar on/before the cutoff
            if bar_date <= cutoff:
                return bar_close
        return None

    perf: dict[str, float] = {}
    if len(bars) > 1:  # 1D = vs the immediately prior bar
        perf["1D"] = _pct(latest_close, bars[1][1])
    for label, lookback in _WINDOWS:
        ref = ref_close(lookback)
        if ref is not None:
            perf[label] = _pct(latest_close, ref)

    return PricePerformance(ticker=ticker, as_of=latest_date, performance=perf)

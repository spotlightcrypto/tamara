"""Tests for prices: bulk ingest and performance computation.

The provider (Polygon) is mocked, so these are hermetic and cost nothing; the
DB side runs against real Supabase like the rest of the suite.
"""

from datetime import date, timedelta

from app.services import prices as svc


def _seed(db, ticker: str, series: dict[int, float]) -> date:
    """Insert bars for `ticker` at the given days-ago -> close, return today."""
    today = date.today()
    rows = [
        {"ticker": ticker, "date": (today - timedelta(days=d)).isoformat(), "close": c}
        for d, c in series.items()
    ]
    db.table("daily_bars").upsert(rows, on_conflict="ticker,date").execute()
    return today


def test_performance_computes_windows(client, db):
    ticker = "ZZPERF"
    # days-ago -> close. Dense enough that each window resolves to its own bar.
    today = _seed(db, ticker, {0: 110.0, 1: 108.0, 7: 100.0, 30: 90.0, 91: 80.0, 182: 70.0, 365: 55.0})

    perf = svc.performance(db, ticker, "XNAS")
    assert perf.as_of == today
    assert perf.price == 110.0  # latest close = current price
    p = perf.performance
    assert p["1D"] == round((110 - 108) / 108 * 100, 2)
    assert p["1W"] == 10.0                       # 110 vs 100
    assert p["1M"] == round((110 - 90) / 90 * 100, 2)
    assert p["3M"] == round((110 - 80) / 80 * 100, 2)
    assert p["6M"] == round((110 - 70) / 70 * 100, 2)
    assert p["1Y"] == 100.0                       # 110 vs 55
    assert "1H" not in p                          # intraday seam, not computed yet

    db.table("daily_bars").delete().eq("ticker", ticker).execute()


def test_performance_since_reference_date(client, db):
    ticker = "ZZSINCE"
    today = _seed(db, ticker, {0: 120.0, 10: 100.0, 30: 80.0})
    since = today - timedelta(days=10)  # narrative "created" 10 days ago
    perf = svc.performance(db, ticker, "XNAS", since=since)
    assert perf.since_date == since
    assert perf.since_close == 100.0
    assert perf.since_change == 20.0  # 120 vs 100
    db.table("daily_bars").delete().eq("ticker", ticker).execute()


def test_performance_omits_windows_without_history(client, db):
    ticker = "ZZSHORT"
    _seed(db, ticker, {0: 50.0, 1: 48.0})  # only two days of data
    perf = svc.performance(db, ticker, "XNAS")
    assert perf.performance["1D"] == round((50 - 48) / 48 * 100, 2)
    assert "1Y" not in perf.performance  # not enough history
    db.table("daily_bars").delete().eq("ticker", ticker).execute()


def test_performance_unknown_ticker_is_empty(client, db):
    perf = svc.performance(db, "NOSUCHTICKER", "XNAS")
    assert perf.as_of is None and perf.performance == {}


def test_performance_uncovered_exchange_is_empty(client, db):
    # A tier-3 / unknown MIC has no free price source: even with bars present under
    # some key, an uncovered listing resolves to no Yahoo symbol -> empty, no error.
    ticker = "ZZPERF"  # has bars seeded in other tests? no — seed our own
    _seed(db, ticker + "X", {0: 100.0, 1: 90.0})
    perf = svc.performance(db, ticker + "X", "ZZZZ")  # ZZZZ = unknown MIC, tier 3
    assert perf.as_of is None and perf.performance == {}
    db.table("daily_bars").delete().eq("ticker", ticker + "X").execute()


def test_ingest_day_bulk_upserts(client, db, monkeypatch):
    day = date(2026, 6, 1)
    monkeypatch.setattr(
        "app.services.prices.prices_provider.grouped_daily",
        lambda d: {"ZZING": 42.0, "ZZING2": 7.5},
    )
    assert svc.ingest_day(db, day) == 2
    row = db.table("daily_bars").select("close").eq("ticker", "ZZING").eq("date", day.isoformat()).execute().data
    assert float(row[0]["close"]) == 42.0
    db.table("daily_bars").delete().in_("ticker", ["ZZING", "ZZING2"]).execute()


def test_performance_endpoint(client, db):
    ticker = "ZZAPI"
    _seed(db, ticker, {0: 120.0, 1: 100.0})
    r = client.get(f"/prices/{ticker}/XNAS/performance")
    assert r.status_code == 200
    assert r.json()["performance"]["1D"] == 20.0
    db.table("daily_bars").delete().eq("ticker", ticker).execute()


def test_performance_requires_auth(unauth_client):
    assert unauth_client.get("/prices/AAPL/XNAS/performance").status_code == 401

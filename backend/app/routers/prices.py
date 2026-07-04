"""HTTP routes for prices.

- Read a ticker's price performance (fast local read from cached bars).
- Trigger a one-day bulk ingest (one API call → the whole market). A daily cron
  can hit this; the initial history backfill runs out-of-band (see the service).
"""

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.auth import CurrentUserDep, UserDbDep
from app.models import PricePerformance
from app.providers.prices import PricesError
from app.services import prices as service

router = APIRouter(tags=["prices"])


@router.get("/prices/{ticker}/performance")
async def get_performance(
    ticker: str, user: CurrentUserDep, db: UserDbDep
) -> PricePerformance:
    """A ticker's percentage performance over the daily windows (1D/1W/1M/3M/6M/1Y)."""
    return service.performance(db, ticker.strip().upper())


@router.post("/prices/ingest")
async def ingest(
    user: CurrentUserDep,
    db: UserDbDep,
    day: date | None = Query(default=None, description="Trading day (YYYY-MM-DD); defaults to today"),
) -> dict[str, int | str]:
    """Bulk-ingest one trading day (all US tickers in a single upstream call)."""
    target = day or date.today()
    try:
        written = service.ingest_day(db, target)
    except PricesError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    return {"date": target.isoformat(), "bars": written}

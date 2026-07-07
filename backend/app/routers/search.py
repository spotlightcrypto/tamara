"""HTTP route for combined search.

`GET /search?q=` returns the caller's matching narratives together with matching
known companies, in one call — the home-page search box. Companies we *don't*
have locally are surfaced separately via `GET /companies/resolve` (external symbol
search), so the frontend can offer "start the first narrative" for them.
"""

from fastapi import APIRouter, Query

from app.auth import UserDbDep
from app.models import SearchResults
from app.services import companies as companies_service
from app.services import narratives as narratives_service

router = APIRouter(tags=["search"])


@router.get("/search")
async def search(
    db: UserDbDep,
    q: str = Query(min_length=1, description="Free text: matches narrative title/thesis and company ticker/name"),
) -> SearchResults:
    """Combined local search: the caller's narratives + globally-known companies."""
    return SearchResults(
        narratives=narratives_service.search(db, q),
        companies=companies_service.search(db, q),
    )

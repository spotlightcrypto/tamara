"""HTTP routes for companies.

Attach/list/detach are nested under a narrative; a single company is fetchable
top-level by id (companies are global, so any signed-in user may read one).
Bare-bones: no search and no hydration yet.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.auth import UserDbDep
from app.models import Company, CompanyAttach, NarrativeSummary, ResolvedListing
from app.providers.prices import PricesError
from app.services import companies as service
from app.services import narratives as narratives_service

router = APIRouter(tags=["companies"])


@router.post(
    "/narratives/{narrative_id}/companies", status_code=status.HTTP_201_CREATED
)
async def attach_company(
    narrative_id: UUID, data: CompanyAttach, db: UserDbDep
) -> Company:
    """Attach a company (by ticker) to a narrative, creating it if new."""
    company = service.attach(db, narrative_id, data)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "narrative not found")
    return company


@router.get("/narratives/{narrative_id}/companies")
async def list_companies(
    narrative_id: UUID, db: UserDbDep
) -> list[Company]:
    """List the companies attached to a narrative."""
    return service.list_for_narrative(db, narrative_id)


@router.delete(
    "/narratives/{narrative_id}/companies/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def detach_company(
    narrative_id: UUID, company_id: UUID, db: UserDbDep
) -> None:
    """Detach a company from a narrative (the company row persists)."""
    if not service.detach(db, narrative_id, company_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "company not attached")


@router.get("/companies/by-symbol/{ticker}/{exchange}")
async def get_company_by_symbol(
    ticker: str, exchange: str, db: UserDbDep
) -> Company:
    """Fetch a company by its slug parts (e.g. CRWV / XNAS) — backs the readable
    /companies/<ticker>:<mic> route. The `exchange` segment may be a MIC, a
    friendly name, or an alias; the service resolves it to a canonical MIC."""
    company = service.get_by_slug(db, ticker, exchange)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "company not found")
    return company


@router.get("/companies/resolve")
async def resolve_companies(
    db: UserDbDep,  # auth-gate only (external call, no DB), keeps the route protected
    q: str = Query(min_length=1, description="Free text: ticker or company name"),
) -> list[ResolvedListing]:
    """Resolve free text to real listings via the external symbol search — how we
    surface a company we don't have locally so the user can start its first
    narrative. Nothing is persisted; attaching later creates the company row."""
    try:
        return service.resolve_external(q)
    except PricesError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))


@router.get("/companies/{company_id}")
async def get_company(
    company_id: UUID, db: UserDbDep
) -> Company:
    """Fetch a single company by id."""
    company = service.get(db, company_id)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "company not found")
    return company


@router.get("/companies/{company_id}/narratives")
async def list_company_narratives(
    company_id: UUID, db: UserDbDep
) -> list[NarrativeSummary]:
    """List the caller's narratives that involve this company (RLS-scoped)."""
    return narratives_service.list_for_company(db, company_id)

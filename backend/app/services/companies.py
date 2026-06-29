"""Business logic for companies and their attachment to narratives.

Companies are a shared/global cache keyed by ticker. Attaching a company to a
narrative is a get-or-create on the company, then a row in the narrative_companies
join. The join is RLS-via-parent; the company rows are globally readable/insertable
by signed-in users (bare-bones).
"""

from uuid import UUID

from supabase import Client

from app.models import Company, CompanyAttach
from app.services import narratives as narratives_service


def _get_or_create_company(db: Client, ticker: str, name: str | None) -> dict:
    """Find the company by ticker, or create it. Returns the raw company row."""
    ticker = ticker.strip().upper()  # normalize, e.g. "nvda" -> "NVDA"
    existing = (
        db.table("companies").select("*").eq("ticker", ticker).limit(1).execute()
    )
    if existing.data:
        return existing.data[0]
    created = (
        db.table("companies")
        .insert({"ticker": ticker, "name": name or ticker})
        .execute()
    )
    return created.data[0]


def attach(db: Client, narrative_id: UUID, data: CompanyAttach) -> Company | None:
    """Attach a company (by ticker) to a narrative. None if the narrative isn't
    owned by the caller (-> 404). Idempotent: re-attaching is a no-op."""
    if not narratives_service.owns(db, narrative_id):
        return None

    company = _get_or_create_company(db, data.ticker, data.name)

    already = (
        db.table("narrative_companies")
        .select("company_id")
        .eq("narrative_id", str(narrative_id))
        .eq("company_id", company["id"])
        .execute()
    )
    if not already.data:
        db.table("narrative_companies").insert(
            {"narrative_id": str(narrative_id), "company_id": company["id"]}
        ).execute()

    return Company.model_validate(company)


def list_for_narrative(db: Client, narrative_id: UUID) -> list[Company]:
    """List the companies attached to a narrative."""
    links = (
        db.table("narrative_companies")
        .select("company_id")
        .eq("narrative_id", str(narrative_id))
        .execute()
    )
    company_ids = [link["company_id"] for link in links.data]
    if not company_ids:
        return []
    companies = db.table("companies").select("*").in_("id", company_ids).execute()
    return [Company.model_validate(row) for row in companies.data]


def detach(db: Client, narrative_id: UUID, company_id: UUID) -> bool:
    """Remove a company from a narrative (the company row itself persists).
    True if a link was removed."""
    response = (
        db.table("narrative_companies")
        .delete()
        .eq("narrative_id", str(narrative_id))
        .eq("company_id", str(company_id))
        .execute()
    )
    return len(response.data) > 0


def get(db: Client, company_id: UUID) -> Company | None:
    """Fetch a single company by id (globally readable)."""
    response = (
        db.table("companies").select("*").eq("id", str(company_id)).limit(1).execute()
    )
    if not response.data:
        return None
    return Company.model_validate(response.data[0])

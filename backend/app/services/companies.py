"""Business logic for companies and their attachment to narratives.

Companies are a shared/global cache keyed by ticker. Attaching a company to a
narrative is a get-or-create on the company, then a row in the narrative_companies
join. The join is RLS-via-parent; the company rows are globally readable/insertable
by signed-in users (bare-bones).
"""

from uuid import UUID

from supabase import Client

from app import exchanges
from app.models import Company, CompanyAttach, ResolvedListing
from app.providers import prices as prices_provider
from app.services import narratives as narratives_service


def _parse_symbol(raw_ticker: str, raw_exchange: str | None) -> tuple[str, str | None]:
    """Normalize an attach request into (ticker, exchange).

    Accepts a bare ticker ("crwv") or an exchange-qualified one ("CRWV:NASDAQ").
    An explicit `exchange` field is used when the ticker isn't qualified.
    """
    raw = raw_ticker.strip().upper()
    exchange = raw_exchange.strip().upper() if raw_exchange and raw_exchange.strip() else None
    if ":" in raw:
        ticker, _, suffix = raw.partition(":")
        return ticker, (suffix or exchange or None)
    return raw, exchange


def _get_or_create_company(
    db: Client, ticker: str, mic: str, meta: dict, name: str | None
) -> dict:
    """Find the company by its (ticker, MIC) identity, or create it. `meta` is the
    exchange-registry metadata (friendly name, currency, country, tier)."""
    existing = (
        db.table("companies")
        .select("*")
        .eq("ticker", ticker)
        .eq("mic", mic)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]
    created = (
        db.table("companies")
        .insert(
            {
                "ticker": ticker,
                "mic": mic,
                "exchange": meta["name"],
                "currency": meta["currency"],
                "country": meta["country"],
                "tier": meta["tier"],
                "name": name or ticker,
            }
        )
        .execute()
    )
    return created.data[0]


def attach(db: Client, narrative_id: UUID, data: CompanyAttach) -> Company | None:
    """Attach a company (by ticker) to a narrative. None if the narrative isn't
    owned by the caller (-> 404). Idempotent: re-attaching is a no-op."""
    if not narratives_service.owns(db, narrative_id):
        return None

    ticker, exchange = _parse_symbol(data.ticker, data.exchange)
    assert exchange is not None  # guaranteed by CompanyAttach's validator
    mic, meta = exchanges.resolve(exchange)  # friendly/alias/MIC -> canonical MIC
    company = _get_or_create_company(db, ticker, mic, meta, data.name)

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


def search(db: Client, q: str, limit: int = 10) -> list[Company]:
    """Search known companies by ticker or name (case-insensitive substring).
    Companies are global, so this isn't user-scoped. Empty query -> []."""
    term = q.strip()
    if not term:
        return []
    safe = term.replace(",", " ").replace("(", " ").replace(")", " ").strip()
    response = (
        db.table("companies")
        .select("*")
        .or_(f"ticker.ilike.*{safe}*,name.ilike.*{safe}*")
        .limit(limit)
        .execute()
    )
    return [Company.model_validate(row) for row in response.data]


def resolve_external(q: str, limit: int = 8) -> list[ResolvedListing]:
    """Resolve free text to real listings via the external symbol search, mapping
    each hit into our (ticker, MIC) model. Used to surface a company we don't have
    locally so the user can start its first narrative. Deduped by (ticker, MIC)."""
    hits = prices_provider.search_symbols(q, limit=limit)
    seen: set[tuple[str, str]] = set()
    out: list[ResolvedListing] = []
    for hit in hits:
        ticker, mic, meta = exchanges.from_yahoo(hit["symbol"], hit.get("exchange"))
        key = (ticker, mic)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            ResolvedListing(
                ticker=ticker,
                mic=mic,
                exchange=meta["name"],
                name=hit["name"],
                currency=meta["currency"],
                tier=meta["tier"],
                has_price=exchanges.yahoo_symbol(ticker, mic) is not None,
            )
        )
    return out


def get(db: Client, company_id: UUID) -> Company | None:
    """Fetch a single company by id (globally readable)."""
    response = (
        db.table("companies").select("*").eq("id", str(company_id)).limit(1).execute()
    )
    if not response.data:
        return None
    return Company.model_validate(response.data[0])


def get_by_slug(db: Client, ticker: str, exchange_or_mic: str) -> Company | None:
    """Fetch a company by its slug parts (ticker + the exchange segment). The
    segment may be a MIC ("xnas"), a friendly name ("nasdaq"), or an alias — we
    resolve it to a canonical MIC first, so both new (ticker:mic) and older
    (ticker:exchange-name) URLs resolve. Case-insensitive on input."""
    mic, _ = exchanges.resolve(exchange_or_mic)
    response = (
        db.table("companies")
        .select("*")
        .eq("ticker", ticker.strip().upper())
        .eq("mic", mic)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return Company.model_validate(response.data[0])

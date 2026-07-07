"""Business logic for narratives.

The service layer sits between routers (HTTP) and the database. Routers stay
thin (parse request, return response); services hold the actual logic and are
the only place that talks to Supabase. This keeps each layer small and testable.

Every function takes a `db` that is already authenticated as the calling user
(see auth.UserDbDep), so Row-Level Security scopes the queries automatically. We
*also* filter/insert by `user_id` explicitly — defense in depth, and it reads
clearly.
"""

from uuid import UUID

from supabase import Client

from app.models import (
    Company,
    Narrative,
    NarrativeCreate,
    NarrativeSummary,
    NarrativeUpdate,
)

# PostgREST embedded-resource select: pull each narrative together with its
# attached companies in ONE query. `narrative_companies(companies(*))` walks the
# join table to the company rows; we flatten them in `_rows_to_summaries`.
_WITH_COMPANIES = "*, narrative_companies(companies(*))"


def _author_map(db: Client, user_ids: set) -> dict[str, str]:
    """Resolve {user_id -> username} from profiles for a set of author ids. We
    look authors up by user_id (immutable) so the username shown is always
    current, even after a rename."""
    ids = [str(u) for u in user_ids if u]
    if not ids:
        return {}
    response = db.table("profiles").select("id,username").in_("id", ids).execute()
    return {row["id"]: row["username"] for row in response.data}


def _with_author(db: Client, model, row: dict):
    """Validate a single narrative row, attaching its author's username."""
    author = _author_map(db, {row.get("user_id")}).get(str(row.get("user_id")))
    return model.model_validate({**row, "author_username": author})


def _rows_to_summaries(db: Client, rows: list[dict]) -> list[NarrativeSummary]:
    """Turn embedded-select rows into NarrativeSummary objects (companies flattened
    from the join, author username resolved from profiles in one batch query)."""
    authors = _author_map(db, {r.get("user_id") for r in rows})
    summaries = []
    for row in rows:
        links = row.pop("narrative_companies", None) or []
        companies = [
            Company.model_validate(link["companies"])
            for link in links
            if link.get("companies")
        ]
        author = authors.get(str(row.get("user_id")))
        summaries.append(
            NarrativeSummary.model_validate({**row, "companies": companies, "author_username": author})
        )
    return summaries


def owns(db: Client, narrative_id: UUID) -> bool:
    """True if the calling user owns this narrative.

    Because `db` is RLS-scoped to the user, the select returns a row only if the
    narrative is theirs. Child resources (items, notes, sources) use this to
    return a clean 404 before writing, instead of letting an insert silently
    fail RLS.
    """
    response = (
        db.table("narratives").select("id").eq("id", str(narrative_id)).limit(1).execute()
    )
    return bool(response.data)


def list_for_user(db: Client, user_id: UUID) -> list[NarrativeSummary]:
    """Return the user's narratives (companies embedded), most recently updated
    first. One query — the companies are joined server-side, so list views don't
    have to fetch companies per narrative."""
    response = (
        db.table("narratives")
        .select(_WITH_COMPANIES)
        .eq("user_id", str(user_id))  # RLS also enforces this; explicit = clear
        .order("updated_at", desc=True)
        .execute()
    )
    return _rows_to_summaries(db, response.data)


def search(db: Client, q: str, limit: int = 10) -> list[NarrativeSummary]:
    """Search the caller's narratives by title/thesis (case-insensitive substring),
    newest first. RLS scopes this to the caller's own rows. Empty query -> []."""
    term = q.strip()
    if not term:
        return []
    # PostgREST `or` with ilike; `*` is the wildcard. Commas/parens in the term
    # would break the filter grammar, so strip them defensively.
    safe = term.replace(",", " ").replace("(", " ").replace(")", " ").strip()
    response = (
        db.table("narratives")
        .select(_WITH_COMPANIES)
        .or_(f"title.ilike.*{safe}*,thesis.ilike.*{safe}*")
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
    )
    return _rows_to_summaries(db, response.data)


def list_for_company(db: Client, company_id: UUID) -> list[NarrativeSummary]:
    """Return the caller's narratives that involve a given company, newest first.

    RLS scopes this to the caller's own narratives automatically. Uses the
    `narrative_companies(company_id)` index to find the narrative ids, then one
    embedded select to hydrate them (with all their companies) in a single query.
    """
    links = (
        db.table("narrative_companies")
        .select("narrative_id")
        .eq("company_id", str(company_id))
        .execute()
    )
    narrative_ids = [link["narrative_id"] for link in links.data]
    if not narrative_ids:
        return []
    response = (
        db.table("narratives")
        .select(_WITH_COMPANIES)
        .in_("id", narrative_ids)  # RLS still filters to the caller's own rows
        .order("updated_at", desc=True)
        .execute()
    )
    return _rows_to_summaries(db, response.data)


def create_for_user(db: Client, user_id: UUID, data: NarrativeCreate) -> Narrative:
    """Insert a new narrative owned by the user and return it."""
    payload = {
        "user_id": str(user_id),
        "title": data.title,
        "thesis": data.thesis,
        "body_md": data.body_md,
        "positioning": data.positioning,
    }
    response = db.table("narratives").insert(payload).execute()
    # insert returns the inserted rows; we created exactly one.
    return _with_author(db, Narrative, response.data[0])


def get_for_user(db: Client, user_id: UUID, narrative_id: UUID) -> Narrative | None:
    """Return one narrative the user owns, or None if it doesn't exist / isn't
    theirs. Returning None (rather than raising) lets the router decide the HTTP
    response — services stay HTTP-agnostic."""
    response = (
        db.table("narratives")
        .select("*")
        .eq("id", str(narrative_id))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return _with_author(db, Narrative, response.data[0])


def update_for_user(
    db: Client, user_id: UUID, narrative_id: UUID, data: NarrativeUpdate
) -> Narrative | None:
    """Apply a partial update and return the updated narrative (or None if not
    found / not owned)."""
    # exclude_unset -> only the fields the client actually sent (PATCH semantics).
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        # Nothing to change: just return the current row (still 404 if missing).
        return get_for_user(db, user_id, narrative_id)

    # updated_at is maintained by a DB trigger (set_updated_at), so we don't
    # stamp it here.
    response = (
        db.table("narratives")
        .update(changes)
        .eq("id", str(narrative_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not response.data:
        return None
    return _with_author(db, Narrative, response.data[0])


def delete_for_user(db: Client, user_id: UUID, narrative_id: UUID) -> bool:
    """Delete a narrative the user owns. Returns True if a row was deleted,
    False if there was nothing to delete (not found / not owned)."""
    response = (
        db.table("narratives")
        .delete()
        .eq("id", str(narrative_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    return len(response.data) > 0

"""Business logic for sources — the external links a narrative is grounded in.

Sources are created during intake finalize (from the kernel's link(s)) and read
on the narrative detail page. RLS-via-parent scopes them through the narrative,
so the `db` client only ever sees sources on narratives the caller owns.
"""

from urllib.parse import urlparse
from uuid import UUID

from supabase import Client

from app.models import Source

_MAX_TITLE = 80  # keep the display name to a "few words" length


def _short_title(url: str, title: str | None) -> str:
    """A tidy display name for a link: the given title (trimmed) or the hostname."""
    clean = (title or "").strip()
    if clean:
        return clean[:_MAX_TITLE]
    host = urlparse(url).hostname or url
    return host[4:] if host.startswith("www.") else host


def add(db: Client, narrative_id: UUID, url: str, title: str | None = None) -> None:
    """Attach a source to a narrative. Idempotent per (narrative, url): a second
    finalize won't duplicate it (unique index + upsert-on-conflict ignore)."""
    payload = {
        "narrative_id": str(narrative_id),
        "url": url.strip(),
        "title": _short_title(url, title),
    }
    # on_conflict = the unique (narrative_id, url) index -> re-finalize is a no-op.
    db.table("sources").upsert(payload, on_conflict="narrative_id,url").execute()


def list_for_narrative(db: Client, narrative_id: UUID) -> list[Source]:
    """List a narrative's sources, oldest first (the kernel link leads)."""
    response = (
        db.table("sources")
        .select("*")
        .eq("narrative_id", str(narrative_id))
        .order("created_at", desc=False)
        .execute()
    )
    return [Source.model_validate(row) for row in response.data]

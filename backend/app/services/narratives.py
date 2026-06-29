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

from app.models import Narrative, NarrativeCreate, NarrativeUpdate


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


def list_for_user(db: Client, user_id: UUID) -> list[Narrative]:
    """Return the user's narratives, most recently updated first."""
    response = (
        db.table("narratives")
        .select("*")
        .eq("user_id", str(user_id))  # RLS also enforces this; explicit = clear
        .order("updated_at", desc=True)
        .execute()
    )
    return [Narrative.model_validate(row) for row in response.data]


def create_for_user(db: Client, user_id: UUID, data: NarrativeCreate) -> Narrative:
    """Insert a new narrative owned by the user and return it."""
    payload = {
        "user_id": str(user_id),
        "title": data.title,
        "thesis": data.thesis,
    }
    response = db.table("narratives").insert(payload).execute()
    # insert returns the inserted rows; we created exactly one.
    return Narrative.model_validate(response.data[0])


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
    return Narrative.model_validate(response.data[0])


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
    return Narrative.model_validate(response.data[0])


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

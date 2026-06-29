"""Business logic for notes.

Notes carry a `user_id` (owner-based RLS), but they also hang off a narrative.
On create we verify the parent narrative is owned by the caller — otherwise a
user could attach a note to someone else's narrative. Reads/edits/deletes are
scoped by RLS (user_id), so the `db` client only ever sees the caller's notes.
"""

from uuid import UUID

from supabase import Client

from app.models import Note, NoteCreate, NoteUpdate
from app.services import narratives as narratives_service


def list_for_narrative(db: Client, narrative_id: UUID) -> list[Note]:
    """List a narrative's notes, newest first."""
    response = (
        db.table("notes")
        .select("*")
        .eq("narrative_id", str(narrative_id))
        .order("created_at", desc=True)
        .execute()
    )
    return [Note.model_validate(row) for row in response.data]


def create(
    db: Client, user_id: UUID, narrative_id: UUID, data: NoteCreate
) -> Note | None:
    """Add a note to a narrative. None if the narrative isn't owned (-> 404)."""
    if not narratives_service.owns(db, narrative_id):
        return None
    payload = {
        "user_id": str(user_id),
        "narrative_id": str(narrative_id),
        "body": data.body,
    }
    response = db.table("notes").insert(payload).execute()
    return Note.model_validate(response.data[0])


def update(db: Client, note_id: UUID, data: NoteUpdate) -> Note | None:
    """Partially update a note. None if not found / not owned."""
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        return get(db, note_id)
    response = db.table("notes").update(changes).eq("id", str(note_id)).execute()
    if not response.data:
        return None
    return Note.model_validate(response.data[0])


def delete(db: Client, note_id: UUID) -> bool:
    """Delete a note. True if a row was deleted."""
    response = db.table("notes").delete().eq("id", str(note_id)).execute()
    return len(response.data) > 0


def get(db: Client, note_id: UUID) -> Note | None:
    """Fetch a single note (RLS-scoped)."""
    response = db.table("notes").select("*").eq("id", str(note_id)).limit(1).execute()
    if not response.data:
        return None
    return Note.model_validate(response.data[0])

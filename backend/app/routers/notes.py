"""HTTP routes for notes.

Create/list are nested under a narrative; edit/delete are top-level by note id.
Same shape as the items router.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.auth import CurrentUserDep, UserDbDep
from app.models import Note, NoteCreate, NoteUpdate
from app.services import notes as service

router = APIRouter(tags=["notes"])


@router.post("/narratives/{narrative_id}/notes", status_code=status.HTTP_201_CREATED)
async def create_note(
    narrative_id: UUID, data: NoteCreate, user: CurrentUserDep, db: UserDbDep
) -> Note:
    """Add a note to a narrative."""
    note = service.create(db, user.id, narrative_id, data)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "narrative not found")
    return note


@router.get("/narratives/{narrative_id}/notes")
async def list_notes(
    narrative_id: UUID, user: CurrentUserDep, db: UserDbDep
) -> list[Note]:
    """List a narrative's notes."""
    return service.list_for_narrative(db, narrative_id)


@router.patch("/notes/{note_id}")
async def update_note(
    note_id: UUID, data: NoteUpdate, user: CurrentUserDep, db: UserDbDep
) -> Note:
    """Edit a note."""
    note = service.update(db, note_id, data)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: UUID, user: CurrentUserDep, db: UserDbDep) -> None:
    """Delete a note."""
    if not service.delete(db, note_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")

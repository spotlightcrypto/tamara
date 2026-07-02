"""HTTP routes for narratives.

An APIRouter groups related endpoints under a common prefix. Routers do HTTP
work only — auth, parsing the request, choosing the status code — then hand off
to the service layer. They never touch the database directly.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.auth import CurrentUserDep, UserDbDep
from app.models import Narrative, NarrativeCreate, NarrativeSummary, NarrativeUpdate
from app.services import narratives as service

router = APIRouter(prefix="/narratives", tags=["narratives"])


@router.get("")
async def list_narratives(user: CurrentUserDep, db: UserDbDep) -> list[NarrativeSummary]:
    """List the calling user's narratives, each with its companies embedded."""
    return service.list_for_user(db, user.id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_narrative(
    data: NarrativeCreate, user: CurrentUserDep, db: UserDbDep
) -> Narrative:
    """Create a narrative owned by the calling user."""
    return service.create_for_user(db, user.id, data)


# `narrative_id: UUID` is a PATH PARAMETER. FastAPI parses it from the URL and
# validates it's a real UUID — a malformed id returns 422 before our code runs.
@router.get("/{narrative_id}")
async def get_narrative(
    narrative_id: UUID, user: CurrentUserDep, db: UserDbDep
) -> Narrative:
    """Fetch one narrative by id."""
    narrative = service.get_for_user(db, user.id, narrative_id)
    if narrative is None:
        # 404 for both "doesn't exist" and "not yours" — never reveal which.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "narrative not found")
    return narrative


@router.patch("/{narrative_id}")
async def update_narrative(
    narrative_id: UUID, data: NarrativeUpdate, user: CurrentUserDep, db: UserDbDep
) -> Narrative:
    """Partially update a narrative (only the fields provided)."""
    narrative = service.update_for_user(db, user.id, narrative_id, data)
    if narrative is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "narrative not found")
    return narrative


@router.delete("/{narrative_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_narrative(
    narrative_id: UUID, user: CurrentUserDep, db: UserDbDep
) -> None:
    """Delete a narrative. Returns 204 No Content on success."""
    if not service.delete_for_user(db, user.id, narrative_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "narrative not found")

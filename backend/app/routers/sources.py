"""HTTP routes for sources.

Sources are created during intake finalize (from the kernel's link[s]); this
router just exposes reading them, nested under a narrative.
"""

from uuid import UUID

from fastapi import APIRouter

from app.auth import CurrentUserDep, UserDbDep
from app.models import Source
from app.services import sources as service

router = APIRouter(tags=["sources"])


@router.get("/narratives/{narrative_id}/sources")
async def list_sources(
    narrative_id: UUID, user: CurrentUserDep, db: UserDbDep
) -> list[Source]:
    """List a narrative's sources (the external links it's grounded in)."""
    return service.list_for_narrative(db, narrative_id)

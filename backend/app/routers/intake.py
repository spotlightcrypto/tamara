"""HTTP routes for the guided narrative intake."""

from fastapi import APIRouter, HTTPException, status

from app.auth import CurrentUserDep, UserDbDep
from app.models import IntakeStart, IntakeState
from app.services import intake as service
from app.services.intake import KernelIngestError

router = APIRouter(tags=["intake"])


@router.post("/narratives/intake", status_code=status.HTTP_201_CREATED)
async def start_intake(
    data: IntakeStart, user: CurrentUserDep, db: UserDbDep
) -> IntakeState:
    """Begin an intake from a kernel: ingest it, then return the first round of
    questions. If a URL kernel can't be read, return a structured 422 so the UI
    can show the error and offer a paste-fallback."""
    try:
        return service.create_draft(db, user.id, data.kernel)
    except KernelIngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "ingest_failed",
                "reason": exc.result.reason.value if exc.result.reason else None,
                "message": "Couldn't read that link. Paste the content instead, or try another URL.",
            },
        )

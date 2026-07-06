"""HTTP routes for the guided narrative intake."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.auth import CurrentUserDep, RequireUsernameDep, UserDbDep
from app.models import (
    IntakeAnswerRequest,
    IntakeFinalize,
    IntakeRegenerate,
    IntakeStart,
    IntakeState,
)
from app.services import intake as service
from app.services.intake import DraftNotFound, KernelIngestError

router = APIRouter(tags=["intake"])


@router.post("/narratives/intake", status_code=status.HTTP_201_CREATED)
async def start_intake(
    data: IntakeStart, user: CurrentUserDep, db: UserDbDep, _username: RequireUsernameDep
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


@router.post("/narratives/intake/{draft_id}/answer")
async def answer_intake(
    draft_id: UUID, data: IntakeAnswerRequest, db: UserDbDep
) -> IntakeState:
    """Submit answers; get the next round of questions or the synthesized proposal."""
    try:
        return service.answer(db, draft_id, data)
    except DraftNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")


@router.get("/narratives/intake/{draft_id}")
async def get_intake(draft_id: UUID, db: UserDbDep) -> IntakeState:
    """Reload an in-progress draft (resume)."""
    try:
        return service.get_draft(db, draft_id)
    except DraftNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")


@router.post("/narratives/intake/{draft_id}/regenerate")
async def regenerate_intake(
    draft_id: UUID, data: IntakeRegenerate, db: UserDbDep
) -> IntakeState:
    """Re-synthesize the proposal from the current (edited) version plus the
    user's free-text instructions. Returns the revised proposal."""
    try:
        return service.regenerate(db, draft_id, data.proposal, data.instructions)
    except DraftNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")


@router.post("/narratives/intake/{draft_id}/finalize", status_code=status.HTTP_201_CREATED)
async def finalize_intake(
    draft_id: UUID, data: IntakeFinalize, user: CurrentUserDep, db: UserDbDep,
    _username: RequireUsernameDep,
) -> dict[str, str]:
    """Accept the (edited) proposal: create the real narrative (markdown body +
    positioning) + companies + sources, and mark the draft finalized. Returns the
    new narrative id."""
    try:
        narrative_id = service.finalize(db, user.id, draft_id, data.proposal)
    except DraftNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")
    return {"narrative_id": str(narrative_id)}

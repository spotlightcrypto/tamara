"""HTTP routes for the caller's profile / username."""

from fastapi import APIRouter, HTTPException, Query, status

from app.auth import CurrentUserDep, UserDbDep
from app.models import Me, Profile, UsernameCheck, UsernameClaim
from app.services import profiles as service
from app.services.profiles import UsernameInvalid, UsernameTaken

router = APIRouter(tags=["profiles"])


@router.get("/me/profile")
async def get_me(user: CurrentUserDep, db: UserDbDep) -> Me:
    """The caller's own identity: their username (null until claimed) + email.
    The only endpoint that returns an email, and only to its owner."""
    profile = service.get_profile(db, user.id)
    return Me(user_id=user.id, email=user.email, username=profile.username if profile else None)


@router.get("/usernames/check")
async def check_username(
    user: CurrentUserDep, db: UserDbDep, u: str = Query(min_length=1, max_length=40)
) -> UsernameCheck:
    """Live availability for a candidate username (UX; the DB is the real gate)."""
    available, reason = service.check_username(db, u)
    return UsernameCheck(available=available, reason=reason)


@router.post("/me/username")
async def set_username(
    data: UsernameClaim, user: CurrentUserDep, db: UserDbDep
) -> Profile:
    """Claim or change the caller's username."""
    try:
        return service.claim_username(db, user.id, data.username)
    except UsernameInvalid as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, exc.reason)
    except UsernameTaken:
        raise HTTPException(status.HTTP_409_CONFLICT, "that username is taken")

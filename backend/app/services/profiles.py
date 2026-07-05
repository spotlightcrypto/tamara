"""Business logic for profiles / usernames.

Usernames are the public identity. We store them LOWERCASE and always reference
users by their immutable id, so a rename is a one-column change that can't break
anything downstream. Uniqueness is enforced by the DB (unique index on
lower(username)); the availability check is just UX.
"""

import re
from uuid import UUID

from supabase import Client

from app.models import Profile

# 3–20 chars, starts with a letter, then letters/digits/underscore.
_USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,19}$")

_RESERVED = {
    "admin", "tamara", "api", "me", "settings", "u", "user", "users", "profile",
    "profiles", "login", "logout", "auth", "null", "none", "root", "support",
    "help", "about", "narratives", "companies", "home",
}


class UsernameInvalid(Exception):
    """The username fails format/reserved rules."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class UsernameTaken(Exception):
    """The username is already claimed by someone else."""


def normalize(raw: str) -> str:
    return raw.strip().lower()


def validate(username: str) -> str | None:
    """Return an error reason if invalid, else None. Expects a normalized value."""
    if not _USERNAME_RE.match(username):
        return "3–20 chars: letters, numbers, or _, and must start with a letter"
    if username.endswith("_"):
        return "can't end with an underscore"
    if username in _RESERVED:
        return "that username is reserved"
    return None


def get_profile(db: Client, user_id: UUID) -> Profile | None:
    """The user's profile, or None if they haven't claimed a username yet."""
    response = db.table("profiles").select("*").eq("id", str(user_id)).limit(1).execute()
    if not response.data:
        return None
    return Profile.model_validate(response.data[0])


def check_username(db: Client, raw: str) -> tuple[bool, str | None]:
    """(available, reason). Validates format then checks the DB for a taken name."""
    username = normalize(raw)
    reason = validate(username)
    if reason:
        return False, reason
    existing = db.table("profiles").select("id").eq("username", username).limit(1).execute()
    if existing.data:
        return False, "taken"
    return True, None


def claim_username(db: Client, user_id: UUID, raw: str) -> Profile:
    """Set (or change) the caller's username. Raises UsernameInvalid on bad
    format, UsernameTaken on a uniqueness collision."""
    username = normalize(raw)
    reason = validate(username)
    if reason:
        raise UsernameInvalid(reason)

    payload = {"id": str(user_id), "username": username}
    try:
        # upsert on the user id: first claim inserts, a later rename updates.
        response = db.table("profiles").upsert(payload, on_conflict="id").execute()
    except Exception as exc:
        # The realistic failure here is the unique(lower(username)) collision.
        raise UsernameTaken() from exc
    return Profile.model_validate(response.data[0])

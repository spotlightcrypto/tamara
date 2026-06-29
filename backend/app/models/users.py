"""User / auth API models."""

from uuid import UUID

from pydantic import BaseModel


class CurrentUser(BaseModel):
    """The authenticated caller, resolved from their bearer token.

    Not a database row — it's the small slice of the Supabase auth user that our
    code actually needs: their id (which scopes everything they own) and email.
    """

    id: UUID
    email: str | None = None

"""Unauthenticated (public) routes.

The rest of the API requires a signed-in user. These routes are deliberately
open — but they use the ANON Supabase client, so Row-Level Security still governs
what's visible. For narratives that means: only PUBLIC ones, and even then we
return just a title + short excerpt. Full content requires signing in.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.db import SupabaseDep
from app.models import NarrativePreview
from app.services import narratives as service

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/narratives/{narrative_id}")
async def public_narrative_preview(
    narrative_id: UUID, db: SupabaseDep
) -> NarrativePreview:
    """Anonymous teaser for a PUBLIC narrative: title + the first ~100 characters.
    No auth required; RLS hides private (and, of course, missing) narratives -> 404.
    The full narrative is available to signed-in users via GET /narratives/{id}."""
    teaser = service.preview(db, narrative_id)
    if teaser is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "narrative not found")
    return teaser

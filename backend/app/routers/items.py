"""HTTP routes for narrative items.

Creation/listing are nested under a narrative (`/narratives/{id}/items`) because
an item only exists in the context of a narrative. Editing a specific item is
top-level (`/items/{item_id}`) since the item id alone identifies it.

Every route takes `user: CurrentUserDep` — even where we don't read `user.id` —
so the token is validated (clean 401) before any database work.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.auth import CurrentUserDep, UserDbDep
from app.models import Item, ItemCreate, ItemKind, ItemMove, ItemUpdate
from app.services import items as service

router = APIRouter(tags=["items"])


@router.post("/narratives/{narrative_id}/items", status_code=status.HTTP_201_CREATED)
async def create_item(
    narrative_id: UUID, data: ItemCreate, user: CurrentUserDep, db: UserDbDep
) -> Item:
    """Add a point to one of the narrative's sections."""
    item = service.create(db, narrative_id, data)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "narrative not found")
    return item


@router.get("/narratives/{narrative_id}/items")
async def list_items(
    narrative_id: UUID,
    user: CurrentUserDep,
    db: UserDbDep,
    kind: ItemKind | None = None,
) -> list[Item]:
    """List a narrative's items, optionally filtered to one section (?kind=bull)."""
    return service.list_for_narrative(db, narrative_id, kind)


@router.patch("/items/{item_id}")
async def update_item(
    item_id: UUID, data: ItemUpdate, user: CurrentUserDep, db: UserDbDep
) -> Item:
    """Edit an item (text, date, or move it to another section via `kind`)."""
    item = service.update(db, item_id, data)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item not found")
    return item


@router.post("/items/{item_id}/move")
async def move_item(
    item_id: UUID, body: ItemMove, user: CurrentUserDep, db: UserDbDep
) -> Item:
    """Reorder an item within its section."""
    item = service.move(db, item_id, body.position)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item not found")
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: UUID, user: CurrentUserDep, db: UserDbDep) -> None:
    """Delete an item."""
    if not service.delete(db, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item not found")

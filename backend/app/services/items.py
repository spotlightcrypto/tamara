"""Business logic for narrative items (bull / bear / catalyst / risk points).

Items have no `user_id`; ownership flows through the parent narrative and is
enforced by RLS-via-parent. The `db` passed in is authenticated as the caller,
so every query is automatically scoped to narratives they own.

`model_dump(mode="json", ...)` is used so enums become strings and dates become
ISO strings — exactly what Supabase/PostgREST wants — without manual conversion.
"""

from uuid import UUID

from supabase import Client

from app.models import Item, ItemCreate, ItemKind, ItemUpdate
from app.services import narratives as narratives_service


def list_for_narrative(
    db: Client, narrative_id: UUID, kind: ItemKind | None = None
) -> list[Item]:
    """List a narrative's items, ordered by section then position. Optionally
    filter to a single section."""
    query = db.table("narrative_items").select("*").eq("narrative_id", str(narrative_id))
    if kind is not None:
        query = query.eq("kind", kind.value)
    response = query.order("kind").order("position").execute()
    return [Item.model_validate(row) for row in response.data]


def create(db: Client, narrative_id: UUID, data: ItemCreate) -> Item | None:
    """Append a new item to the end of its section. Returns None if the parent
    narrative doesn't exist / isn't owned (-> router 404)."""
    if not narratives_service.owns(db, narrative_id):
        return None

    # Next position = (highest current position in this section) + 1, else 0.
    last = (
        db.table("narrative_items")
        .select("position")
        .eq("narrative_id", str(narrative_id))
        .eq("kind", data.kind.value)
        .order("position", desc=True)
        .limit(1)
        .execute()
    )
    next_position = last.data[0]["position"] + 1 if last.data else 0

    payload = data.model_dump(mode="json")
    payload["narrative_id"] = str(narrative_id)
    payload["position"] = next_position

    response = db.table("narrative_items").insert(payload).execute()
    return Item.model_validate(response.data[0])


def update(db: Client, item_id: UUID, data: ItemUpdate) -> Item | None:
    """Partially update an item. Returns None if not found / not owned."""
    changes = data.model_dump(mode="json", exclude_unset=True)
    if not changes:
        return get(db, item_id)

    response = (
        db.table("narrative_items").update(changes).eq("id", str(item_id)).execute()
    )
    if not response.data:
        return None
    return Item.model_validate(response.data[0])


def move(db: Client, item_id: UUID, position: int) -> Item | None:
    """Set an item's position within its section. Returns None if not found."""
    response = (
        db.table("narrative_items")
        .update({"position": position})
        .eq("id", str(item_id))
        .execute()
    )
    if not response.data:
        return None
    return Item.model_validate(response.data[0])


def delete(db: Client, item_id: UUID) -> bool:
    """Delete an item. True if a row was deleted, False if there was none."""
    response = db.table("narrative_items").delete().eq("id", str(item_id)).execute()
    return len(response.data) > 0


def get(db: Client, item_id: UUID) -> Item | None:
    """Fetch a single item (RLS-scoped). Used by update's no-op path."""
    response = (
        db.table("narrative_items").select("*").eq("id", str(item_id)).limit(1).execute()
    )
    if not response.data:
        return None
    return Item.model_validate(response.data[0])

"""Cross-user visibility: what one signed-in user can and can't see of another's
narratives. Uses two REAL-auth clients (no dependency overrides) so the two
identities are genuinely distinct:

  - real_client2  -> user 2 ("tester2"), the AUTHOR
  - real_client   -> user 1 ("tester1"), the VIEWER

RLS is the thing under test: public narratives are readable/searchable by anyone;
private ones are owner-only; and no one but the owner can edit or delete.
"""

import uuid

import pytest


@pytest.fixture
def author_narrative(real_client2):
    """Create narratives owned by user 2, cleaned up after the test."""
    created: list[str] = []

    def _make(is_public: bool = True, title: str | None = None, body_md: str = "") -> dict:
        payload = {
            "title": title or f"XV {uuid.uuid4().hex[:12]}",
            "is_public": is_public,
            "body_md": body_md,
        }
        r = real_client2.post("/narratives", json=payload)
        assert r.status_code == 201, r.text
        n = r.json()
        created.append(n["id"])
        return n

    yield _make

    for nid in created:
        real_client2.delete(f"/narratives/{nid}")


def test_public_narrative_visible_to_other_user(author_narrative, real_client):
    n = author_narrative(is_public=True, body_md="the whole thesis body")
    r = real_client.get(f"/narratives/{n['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["author_username"] == "tester2"  # it's the other user's
    assert body["body_md"] == "the whole thesis body"  # full content, not a teaser


def test_private_narrative_hidden_from_other_user(author_narrative, real_client):
    n = author_narrative(is_public=False)
    assert real_client.get(f"/narratives/{n['id']}").status_code == 404


def test_owner_still_sees_own_private_narrative(author_narrative, real_client2):
    n = author_narrative(is_public=False)
    assert real_client2.get(f"/narratives/{n['id']}").status_code == 200


def test_search_surfaces_others_public_narrative(author_narrative, real_client):
    token = f"zzxv{uuid.uuid4().hex[:8]}"
    n = author_narrative(is_public=True, title=f"Public {token} take")
    hits = real_client.get("/search", params={"q": token}).json()
    assert n["id"] in [x["id"] for x in hits["narratives"]]


def test_search_excludes_others_private_narrative(author_narrative, real_client):
    token = f"zzxv{uuid.uuid4().hex[:8]}"
    n = author_narrative(is_public=False, title=f"Private {token} take")
    hits = real_client.get("/search", params={"q": token}).json()
    assert n["id"] not in [x["id"] for x in hits["narratives"]]


def test_other_user_cannot_edit_or_delete(author_narrative, real_client, real_client2):
    # A public narrative is readable by others but writable only by its owner.
    n = author_narrative(is_public=True, title="Owned by tester2")
    assert real_client.patch(f"/narratives/{n['id']}", json={"title": "hijacked"}).status_code == 404
    assert real_client.delete(f"/narratives/{n['id']}").status_code == 404
    # Still intact and unchanged for the owner.
    owner_view = real_client2.get(f"/narratives/{n['id']}").json()
    assert owner_view["title"] == "Owned by tester2"

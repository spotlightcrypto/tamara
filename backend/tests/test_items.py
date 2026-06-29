"""Tests for narrative items (bull / bear / catalyst / risk).

Items are created under a narrative made by `make_narrative`; deleting that
narrative in fixture teardown cascades to its items, so no extra cleanup needed.
"""

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def _add(client, narrative_id, kind="bull", body="a point", event_date=None):
    payload = {"kind": kind, "body": body}
    if event_date is not None:
        payload["event_date"] = event_date
    return client.post(f"/narratives/{narrative_id}/items", json=payload)


def test_create_item_in_each_section(client, make_narrative):
    n = make_narrative()
    for kind in ("bull", "bear", "catalyst", "risk"):
        r = _add(client, n["id"], kind=kind, body=f"{kind} point")
        assert r.status_code == 201
        body = r.json()
        assert body["kind"] == kind
        assert body["narrative_id"] == n["id"]
        assert body["position"] == 0  # first in its section


def test_items_append_in_position_order(client, make_narrative):
    n = make_narrative()
    first = _add(client, n["id"], "bull", "first").json()
    second = _add(client, n["id"], "bull", "second").json()
    assert first["position"] == 0
    assert second["position"] == 1


def test_list_and_filter_by_kind(client, make_narrative):
    n = make_narrative()
    _add(client, n["id"], "bull", "b1")
    _add(client, n["id"], "risk", "r1")
    all_items = client.get(f"/narratives/{n['id']}/items").json()
    assert len(all_items) == 2
    bulls = client.get(f"/narratives/{n['id']}/items?kind=bull").json()
    assert len(bulls) == 1 and bulls[0]["kind"] == "bull"


def test_create_rejects_unknown_kind(client, make_narrative):
    n = make_narrative()
    assert _add(client, n["id"], kind="moon", body="x").status_code == 422


def test_create_rejects_empty_body(client, make_narrative):
    n = make_narrative()
    assert _add(client, n["id"], "bull", body="").status_code == 422


def test_create_on_missing_narrative_returns_404(client):
    assert _add(client, MISSING_ID, "bull", "x").status_code == 404


def test_catalyst_can_carry_a_date(client, make_narrative):
    n = make_narrative()
    item = _add(client, n["id"], "catalyst", "Q3 earnings", event_date="2026-08-01").json()
    assert item["event_date"] == "2026-08-01"


def test_patch_updates_body(client, make_narrative):
    n = make_narrative()
    item = _add(client, n["id"], "bull", "old").json()
    r = client.patch(f"/items/{item['id']}", json={"body": "new"})
    assert r.status_code == 200 and r.json()["body"] == "new"


def test_patch_advances_updated_at(client, make_narrative):
    n = make_narrative()
    item = _add(client, n["id"], "bull", "x").json()
    assert item["created_at"] == item["updated_at"]  # equal at creation
    updated = client.patch(f"/items/{item['id']}", json={"body": "y"}).json()
    assert updated["updated_at"] != item["updated_at"]  # trigger advanced it


def test_patch_kind_moves_between_sections(client, make_narrative):
    n = make_narrative()
    item = _add(client, n["id"], "bull", "x").json()
    r = client.patch(f"/items/{item['id']}", json={"kind": "bear"})
    assert r.status_code == 200 and r.json()["kind"] == "bear"


def test_move_changes_position(client, make_narrative):
    n = make_narrative()
    item = _add(client, n["id"], "bull", "x").json()
    r = client.post(f"/items/{item['id']}/move", json={"position": 5})
    assert r.status_code == 200 and r.json()["position"] == 5


def test_delete_removes_item(client, make_narrative):
    n = make_narrative()
    item = _add(client, n["id"], "bull", "x").json()
    assert client.delete(f"/items/{item['id']}").status_code == 204
    remaining = [i["id"] for i in client.get(f"/narratives/{n['id']}/items").json()]
    assert item["id"] not in remaining


def test_patch_missing_item_returns_404(client):
    assert client.patch(f"/items/{MISSING_ID}", json={"body": "x"}).status_code == 404


def test_move_missing_item_returns_404(client):
    assert client.post(f"/items/{MISSING_ID}/move", json={"position": 1}).status_code == 404


def test_delete_missing_item_returns_404(client):
    assert client.delete(f"/items/{MISSING_ID}").status_code == 404


def test_items_require_auth(unauth_client):
    assert unauth_client.get(f"/narratives/{MISSING_ID}/items").status_code == 401

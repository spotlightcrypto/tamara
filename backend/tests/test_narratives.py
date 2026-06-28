"""Tests for the narratives CRUD endpoints.

Each test names what it checks. They don't assume an empty database — they find
the rows they created by id, so pre-existing data doesn't break them.
"""

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def test_create_returns_201_with_server_fields(make_narrative):
    n = make_narrative(title="Bull thesis", thesis="long power names")
    assert n["title"] == "Bull thesis"
    assert n["thesis"] == "long power names"
    # Server-generated fields are present.
    assert n["id"] and n["created_at"] and n["updated_at"]


def test_create_requires_a_title(client):
    assert client.post("/narratives", json={"thesis": "no title"}).status_code == 422


def test_list_includes_created_narrative(client, make_narrative):
    n = make_narrative(title="Findable")
    ids = [item["id"] for item in client.get("/narratives").json()]
    assert n["id"] in ids


def test_get_by_id_returns_the_narrative(client, make_narrative):
    n = make_narrative()
    response = client.get(f"/narratives/{n['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == n["id"]


def test_get_missing_returns_404(client):
    assert client.get(f"/narratives/{MISSING_ID}").status_code == 404


def test_get_malformed_id_returns_422(client):
    assert client.get("/narratives/not-a-uuid").status_code == 422


def test_patch_updates_only_supplied_fields(client, make_narrative):
    n = make_narrative(title="Keep me", thesis="old")
    response = client.patch(f"/narratives/{n['id']}", json={"thesis": "new"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Keep me"          # untouched
    assert body["thesis"] == "new"             # changed
    assert body["updated_at"] != n["updated_at"]  # timestamp advanced


def test_patch_rejects_empty_title(client, make_narrative):
    n = make_narrative()
    assert client.patch(f"/narratives/{n['id']}", json={"title": ""}).status_code == 422


def test_patch_missing_returns_404(client):
    assert client.patch(f"/narratives/{MISSING_ID}", json={"thesis": "x"}).status_code == 404


def test_delete_then_get_is_404(client, make_narrative):
    n = make_narrative()
    assert client.delete(f"/narratives/{n['id']}").status_code == 204
    assert client.get(f"/narratives/{n['id']}").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete(f"/narratives/{MISSING_ID}").status_code == 404

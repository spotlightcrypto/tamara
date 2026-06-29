"""Tests for notes. Notes cascade-delete with their parent narrative, which
`make_narrative` cleans up — so no separate note cleanup is needed."""

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def _add(client, narrative_id, body="a note"):
    return client.post(f"/narratives/{narrative_id}/notes", json={"body": body})


def test_create_note(client, make_narrative):
    n = make_narrative()
    r = _add(client, n["id"], "first thoughts")
    assert r.status_code == 201
    note = r.json()
    assert note["body"] == "first thoughts"
    assert note["narrative_id"] == n["id"]
    assert note["created_at"] == note["updated_at"]


def test_create_rejects_empty_body(client, make_narrative):
    n = make_narrative()
    assert _add(client, n["id"], body="").status_code == 422


def test_create_on_missing_narrative_returns_404(client):
    assert _add(client, MISSING_ID).status_code == 404


def test_list_returns_notes(client, make_narrative):
    n = make_narrative()
    _add(client, n["id"], "one")
    _add(client, n["id"], "two")
    notes = client.get(f"/narratives/{n['id']}/notes").json()
    assert len(notes) == 2
    assert {note["body"] for note in notes} == {"one", "two"}


def test_patch_updates_body_and_advances_updated_at(client, make_narrative):
    n = make_narrative()
    note = _add(client, n["id"], "old").json()
    updated = client.patch(f"/notes/{note['id']}", json={"body": "new"}).json()
    assert updated["body"] == "new"
    assert updated["updated_at"] != note["updated_at"]


def test_delete_note(client, make_narrative):
    n = make_narrative()
    note = _add(client, n["id"]).json()
    assert client.delete(f"/notes/{note['id']}").status_code == 204
    assert note["id"] not in [x["id"] for x in client.get(f"/narratives/{n['id']}/notes").json()]


def test_patch_missing_note_returns_404(client):
    assert client.patch(f"/notes/{MISSING_ID}", json={"body": "x"}).status_code == 404


def test_delete_missing_note_returns_404(client):
    assert client.delete(f"/notes/{MISSING_ID}").status_code == 404


def test_notes_require_auth(unauth_client):
    assert unauth_client.get(f"/narratives/{MISSING_ID}/notes").status_code == 401

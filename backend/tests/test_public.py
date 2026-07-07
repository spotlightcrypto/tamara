"""Tests for the unauthenticated public preview.

A logged-OUT visitor may see a PUBLIC narrative's title + first ~100 chars only.
Private narratives are invisible (RLS), and the full authed endpoint stays 401.
We create rows with the authed `client`, then read them with `unauth_client`
(no overrides -> real anon path).
"""

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def test_public_preview_of_public_narrative(client, unauth_client, make_narrative):
    n = make_narrative(title="Power demand supercycle", thesis="grid can't keep up")
    r = unauth_client.get(f"/public/narratives/{n['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Power demand supercycle"
    assert body["preview"]  # non-empty excerpt
    # Never leak the full content to an anonymous caller.
    assert "body_md" not in body and "thesis" not in body


def test_public_preview_caps_at_100_chars(client, unauth_client):
    long_body = "x" * 250
    n = client.post(
        "/narratives", json={"title": "Long take", "body_md": long_body}
    ).json()
    r = unauth_client.get(f"/public/narratives/{n['id']}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["preview"]) == 100
    assert body["truncated"] is True
    client.delete(f"/narratives/{n['id']}")


def test_public_preview_hides_private_narrative(client, unauth_client):
    n = client.post(
        "/narratives", json={"title": "Secret", "is_public": False}
    ).json()
    # Anon can't see a private narrative at all -> 404 (not a partial leak).
    assert unauth_client.get(f"/public/narratives/{n['id']}").status_code == 404
    client.delete(f"/narratives/{n['id']}")


def test_public_preview_missing_is_404(unauth_client):
    assert unauth_client.get(f"/public/narratives/{MISSING_ID}").status_code == 404


def test_full_narrative_still_requires_auth(unauth_client):
    # The full (non-preview) endpoint must remain closed to anonymous callers.
    # (No `client` fixture here — it installs global auth overrides that would
    # otherwise leak into this unauthenticated request.)
    assert unauth_client.get(f"/narratives/{MISSING_ID}").status_code == 401

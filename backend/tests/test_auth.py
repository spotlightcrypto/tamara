"""Tests for the authentication boundary.

These use `unauth_client` (no dependency overrides), so the real auth runs and
should reject anything without a valid token.
"""


def test_list_narratives_requires_auth(unauth_client):
    assert unauth_client.get("/narratives").status_code == 401


def test_me_requires_auth(unauth_client):
    assert unauth_client.get("/me").status_code == 401


def test_bad_token_is_rejected(unauth_client):
    response = unauth_client.get(
        "/narratives", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_create_requires_auth(unauth_client):
    assert unauth_client.post("/narratives", json={"title": "x"}).status_code == 401

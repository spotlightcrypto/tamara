"""Shared pytest fixtures.

`conftest.py` is special: pytest auto-discovers it, and any fixture defined here
is available to every test file without importing it.

Our endpoints normally require a real Supabase JWT. Rather than mint and verify
one on every call, we use FastAPI's `app.dependency_overrides` to swap the auth
dependencies for test versions:

  - `get_current_user` -> returns a fixed test user (no JWT verification)
  - `get_user_db`      -> a Supabase client authenticated as that test user

So requests through the `client` fixture are "logged in" as the test user, and
database calls are real (and RLS-scoped) — these are integration tests.
"""

import pytest
from fastapi.testclient import TestClient
from supabase import create_client

from app.auth import get_current_user, get_user_db
from app.config import settings
from app.db import make_user_client
from app.main import app
from app.models import CurrentUser

TEST_EMAIL = "tamara.dev.test@gmail.com"
TEST_PASSWORD = "Test-pass-123456"


@pytest.fixture(scope="session")
def auth() -> dict:
    """Sign in the test user once per test session; return their id + token."""
    sb = create_client(settings.supabase_url, settings.supabase_anon_key)
    session = sb.auth.sign_in_with_password(
        {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    ).session
    return {"user_id": session.user.id, "token": session.access_token}


@pytest.fixture
def client(auth: dict):
    """A TestClient authenticated as the test user via dependency overrides."""
    test_user = CurrentUser(id=auth["user_id"], email=TEST_EMAIL)

    # The override functions take no params, so requests need no Authorization
    # header — FastAPI calls these instead of the real dependencies.
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_user_db] = lambda: make_user_client(auth["token"])

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()  # always reset, even if a test failed


@pytest.fixture
def unauth_client():
    """A TestClient with NO overrides — the real auth runs, so it rejects
    requests without a valid token. Used to test the security boundary."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_narrative(client: TestClient):
    """Factory that creates narratives and cleans them up after the test,
    even if the test fails (cleanup runs after the `yield`)."""
    created_ids: list[str] = []

    def _make(title: str = "Test narrative", thesis: str = "") -> dict:
        response = client.post("/narratives", json={"title": title, "thesis": thesis})
        assert response.status_code == 201
        data = response.json()
        created_ids.append(data["id"])
        return data

    yield _make

    for narrative_id in created_ids:
        client.delete(f"/narratives/{narrative_id}")

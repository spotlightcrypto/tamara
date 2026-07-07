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

from app.auth import get_current_user, get_user_db, require_username
from app.config import settings
from app.db import make_user_client
from app.main import app
from app.models import CurrentUser

TEST_EMAIL = "tamara.dev.test@gmail.com"
TEST_PASSWORD = "Test-pass-123456"
# A SECOND real user (username "tester2"), used to test cross-user visibility —
# what one user can/can't see of another's narratives.
#
# One-time provisioning (against a fresh Supabase project, keep both users):
#   1. Sign up:  supabase.auth.sign_up({email, password}) with the anon key.
#   2. Confirm:  update auth.users set email_confirmed_at = now() where email = …
#   3. Username: insert into public.profiles (id, username)
#                select id, 'tester2' from auth.users where email = …
# (User 1 gets 'tester1' the same way; test_profiles wipes user 1's profile each
# run, but the visibility tests only need user 2's username to persist.)
TEST_EMAIL_2 = "tamara.dev.test2@gmail.com"
TEST_PASSWORD_2 = "Test-pass-2-123456"


@pytest.fixture(scope="session")
def auth() -> dict:
    """Sign in the test user once per test session; return their id + token."""
    sb = create_client(settings.supabase_url, settings.supabase_anon_key)
    session = sb.auth.sign_in_with_password(
        {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    ).session
    return {"user_id": session.user.id, "token": session.access_token}


@pytest.fixture(scope="session")
def auth2() -> dict:
    """Sign in the SECOND test user once per session; return their id + token."""
    sb = create_client(settings.supabase_url, settings.supabase_anon_key)
    session = sb.auth.sign_in_with_password(
        {"email": TEST_EMAIL_2, "password": TEST_PASSWORD_2}
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
    # Bypass the username gate so the many create-content tests don't each need a
    # claimed username; the gate itself is tested separately via `gated_client`.
    app.dependency_overrides[require_username] = lambda: "tester"

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()  # always reset, even if a test failed


@pytest.fixture
def gated_client(auth: dict):
    """Like `client` but WITHOUT the username-gate bypass — for testing the gate."""
    test_user = CurrentUser(id=auth["user_id"], email=TEST_EMAIL)
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_user_db] = lambda: make_user_client(auth["token"])
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client():
    """A TestClient with NO overrides — the real auth runs, so it rejects
    requests without a valid token. Used to test the security boundary."""
    with TestClient(app) as c:
        yield c


# --- Real-auth clients for multi-user tests -----------------------------------
#
# The `client` fixture installs GLOBAL dependency overrides, so it can only ever
# be one identity at a time — no good for "can user A see user B's data?". These
# clients instead carry a real bearer token and run the REAL auth path (no
# overrides), so two of them can act as two different users in the same test.

@pytest.fixture
def real_client(auth: dict):
    """User 1 via the real auth path (bearer token, no overrides)."""
    with TestClient(app, headers={"Authorization": f"Bearer {auth['token']}"}) as c:
        yield c


@pytest.fixture
def real_client2(auth2: dict):
    """User 2 via the real auth path (bearer token, no overrides)."""
    with TestClient(app, headers={"Authorization": f"Bearer {auth2['token']}"}) as c:
        yield c


@pytest.fixture
def db(auth: dict):
    """A Supabase client authed as the test user — for direct DB checks/cleanup
    in tests (e.g. inspecting a draft's transcript)."""
    return make_user_client(auth["token"])


@pytest.fixture
def user_id(auth: dict) -> str:
    return auth["user_id"]


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

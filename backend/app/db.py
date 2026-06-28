"""Supabase client wiring.

We build ONE Supabase client from our settings and hand it to routes through
FastAPI's dependency-injection system. A route never constructs its own client;
it declares "I need the database" and FastAPI provides it. That keeps routes
testable (we can swap the dependency in tests) and avoids reconnecting per call.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from supabase import Client, create_client

from app.config import settings


@lru_cache
def get_supabase() -> Client:
    """Build (once) and return the shared Supabase client.

    `@lru_cache` makes this a singleton: the first call creates the client,
    every later call returns that same instance. We use the public (anon /
    publishable) key — access is governed by Row-Level Security in the database.
    """
    return create_client(settings.supabase_url, settings.supabase_anon_key)


# A reusable, typed dependency. Read it as: "a Supabase `Client`, obtained by
# calling `get_supabase` via Depends". Any route parameter annotated with
# `SupabaseDep` gets the client injected automatically.
SupabaseDep = Annotated[Client, Depends(get_supabase)]


def make_user_client(access_token: str) -> Client:
    """Build a per-request Supabase client that acts AS the calling user.

    The shared `get_supabase()` client uses the anon key and carries no user
    identity, so Row-Level Security would hide (and block) every row. Here we
    attach the user's JWT, so PostgREST runs each query as that user and RLS
    lets them read/write exactly their own rows.

    One client per request — cheap to build, and it avoids sharing one user's
    token across concurrent requests (which mutating the singleton would risk).
    """
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)  # send this JWT on every PostgREST call
    return client

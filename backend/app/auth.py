"""Authentication: turning an incoming request into a known user.

We verify the Supabase access token LOCALLY — no network round-trip per request.
Supabase signs tokens with ES256 (asymmetric) and publishes the matching PUBLIC
keys at a JWKS endpoint. We fetch those keys (cached), verify each token's
signature ourselves, and read the user id straight from the token's claims.

Two small dependencies share ONE token extraction (FastAPI caches it per
request, so the header is parsed once):
  - get_current_user -> who is calling (validated locally)
  - get_user_db      -> a Supabase client authenticated as that user (for RLS)
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from supabase import Client

from app.config import settings
from app.db import make_user_client
from app.models import CurrentUser

# Pulls the token from the "Authorization: Bearer <jwt>" header (and adds the
# Authorize button to /docs). Missing/malformed header -> 401 before our code.
_bearer = HTTPBearer()

# Supabase publishes its public signing keys here. PyJWKClient fetches them once
# and caches the set (default ~5 min), refetching automatically if it sees a key
# id (`kid`) it doesn't know — which transparently handles key rotation. So this
# is effectively "no network per request", unlike calling auth.get_user.
_jwks_client = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")

# Every Supabase access token carries these; we reject anything that doesn't
# match, as a guard against misrouted or forged tokens.
_AUDIENCE = "authenticated"
_ISSUER = f"{settings.supabase_url}/auth/v1"


def get_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> str:
    """Extract the raw bearer token. Both dependencies below depend on this, so
    FastAPI's per-request caching means the header is parsed exactly once."""
    return credentials.credentials


AccessTokenDep = Annotated[str, Depends(get_access_token)]


def get_current_user(token: AccessTokenDep) -> CurrentUser:
    """Verify the JWT locally (signature, expiry, audience, issuer) and return
    the calling user. No network call — the public key is cached."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],   # pin the algorithm — never let the token pick it
            audience=_AUDIENCE,
            issuer=_ISSUER,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
        )
    # `sub` is the user's id; `email` is present on Supabase tokens.
    return CurrentUser(id=claims["sub"], email=claims.get("email"))


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def get_user_db(token: AccessTokenDep) -> Client:
    """Per-request Supabase client authenticated as the caller, for RLS-scoped
    data access. Pair it with CurrentUserDep on data routes: that dependency
    verifies the token; this one attaches it to the database client."""
    return make_user_client(token)


UserDbDep = Annotated[Client, Depends(get_user_db)]


def require_username(user: CurrentUserDep, db: UserDbDep) -> str:
    """Gate for content creation: a user must have claimed a username before they
    can create/post. Returns the username, or 403s. Defense-in-depth alongside the
    frontend first-login gate."""
    from app.services import profiles as profiles_service  # local import: avoid cycle

    profile = profiles_service.get_profile(db, user.id)
    if profile is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "set a username before creating or posting"
        )
    return profile.username


# Add this dependency to any create/post endpoint to enforce the username gate.
RequireUsernameDep = Annotated[str, Depends(require_username)]

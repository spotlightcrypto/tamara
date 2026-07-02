"""Tamara backend — entry point.

For now this is just a hello-world FastAPI app so we can confirm the whole
toolchain (venv → FastAPI → uvicorn) works end to end. We'll grow it one small
step at a time.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth import CurrentUserDep
from app.config import settings
from app.db import SupabaseDep
from app.models import CurrentUser
from app.routers.companies import router as companies_router
from app.routers.intake import router as intake_router
from app.routers.items import router as items_router
from app.routers.narratives import router as narratives_router
from app.routers.notes import router as notes_router
from app.routers.sources import router as sources_router

# `app` is the FastAPI application object. uvicorn looks for this object (by the
# import path "app.main:app") and serves it.
app = FastAPI(title="Tamara API")

# CORS: browsers block cross-origin requests unless the server opts in. The Vite
# dev server runs on a different origin (localhost:5173) than the API
# (localhost:8000), so we must allow it. In dev we allow localhost; tighten this
# to the real frontend origin in production.
_dev_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins if settings.app_env == "dev" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the feature routers onto the app.
app.include_router(narratives_router)
app.include_router(items_router)
app.include_router(notes_router)
app.include_router(companies_router)
app.include_router(sources_router)
app.include_router(intake_router)


# A "route": when an HTTP GET request hits the path "/", FastAPI calls this
# function and sends whatever it returns back as JSON.
#
# `@app.get("/")` is a *decorator* — it registers the function below as the
# handler for GET /. The function is `async` because FastAPI is built on async
# I/O; for now the body does no awaiting, which is perfectly fine.
@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Tamara backend is alive"}


# `db: SupabaseDep` is dependency injection in action: FastAPI sees the
# annotation, calls `get_supabase()` for us, and passes the client in. The
# route just uses it.
@app.get("/health")
async def health(db: SupabaseDep) -> dict[str, str]:
    # One trivial round-trip to Supabase to prove the backend can reach it.
    # (supabase-py is synchronous; this briefly blocks the event loop, which is
    # fine for a health check — we'll use async patterns where it matters.)
    try:
        db.storage.list_buckets()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unreachable: {exc}") from exc
    return {"status": "ok", "db": "ok"}


# A protected route: depending on `CurrentUserDep` means a valid bearer token is
# required. FastAPI resolves get_current_user first; if it raises, this body
# never runs. Returns whoever is calling.
@app.get("/me")
async def me(user: CurrentUserDep) -> CurrentUser:
    return user

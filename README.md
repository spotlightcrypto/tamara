# Tamara

A personal investment-research agent. You keep **narratives** (investment theses); each pulls
together the **companies** it's about, your **notes** and **sources**, and four sections —
**bull case, bear case, catalysts, risks**. An agent helps you draft and fill them in, on
request.

This is also a deliberate **Python learning project**: the backend is built in small,
reviewable increments.

## Stack
- **Backend:** Python + FastAPI, Supabase (Postgres + Auth, Row-Level Security)
- **Frontend:** TypeScript + React _(not started yet)_
- **Agent:** provider-agnostic LLM gateway (Claude by default)

## Repository layout
```
spec/        Implementation spec (architecture, data model, API, agent, build plan, ...)
backend/     FastAPI app
  app/         config, db, auth, models, routers/, services/
  migrations/  SQL migrations (source of truth)
  tests/       pytest suite
```
See [`spec/README.md`](spec/README.md) for the full design.

## Backend — getting started
```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env          # then fill in Supabase URL + anon key
.venv/bin/python -m uvicorn app.main:app --reload
```
Interactive API docs: http://127.0.0.1:8000/docs

Run the tests:
```bash
cd backend
.venv/bin/python -m pytest
```

## Current status
Backend foundations are in place: typed settings, Supabase client + auth (local JWT
verification), and full **narratives** CRUD behind Row-Level Security, with a pytest suite.
Next: section items (bull/bear/catalyst/risk), then notes, sources, companies, and the agent.

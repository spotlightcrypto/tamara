# 02 — API Contracts

REST over HTTPS, JSON in/out. All routes (except `/health`) require
`Authorization: Bearer <supabase-jwt>`. The backend extracts `user_id` from the JWT; clients
never send `user_id` in bodies. Errors use standard HTTP codes with
`{ "detail": "<message>" }`.

Conventions:
- `404` when a resource doesn't exist *or* isn't owned by the caller (don't leak existence).
- `401` missing/invalid JWT; `403` valid JWT but not permitted; `422` validation error
  (FastAPI/Pydantic default).
- Timestamps are ISO-8601 UTC. IDs are UUID strings.
- List endpoints return `{ "items": [...] }` (room to add pagination later).

---

## Health
```
GET /health → 200 { "status": "ok", "db": "ok" }   # does one trivial Supabase query
```

## Narratives
```
GET  /narratives
  → 200 { items: [ NarrativeSummary ] }             # caller's narratives, recent first

POST /narratives
  body: { title: string, thesis?: string }
  → 201 Narrative                                    # blank-form creation path

GET  /narratives/{id}
  → 200 NarrativeDetail                              # narrative + items + companies + sources + notes

PATCH /narratives/{id}
  body: { title?: string, thesis?: string }
  → 200 Narrative

DELETE /narratives/{id}
  → 204
```

`NarrativeSummary`: `{ id, title, thesis, company_count, updated_at }`
`NarrativeDetail`: `{ id, title, thesis, created_at, updated_at, items: [Item], companies:
[CompanyChip], sources: [Source], notes: [Note] }`

## Section items (bull / bear / catalyst / risk)
```
POST /narratives/{id}/items
  body: { kind: 'bull'|'bear'|'catalyst'|'risk', body: string,
          source_id?: uuid, event_date?: date }
  → 201 Item                                         # appended at end of its section

PATCH /items/{item_id}
  body: { body?, source_id?, event_date?, kind? }
  → 200 Item

POST /items/{item_id}/move
  body: { position: int }                            # reorder within its section
  → 200 Item

DELETE /items/{item_id}
  → 204
```

`Item`: `{ id, narrative_id, kind, body, source_id, event_date, position, created_at }`

## Notes
```
POST /narratives/{id}/notes
  body: { body: string, company_id?: uuid }
  → 201 Note
PATCH  /notes/{note_id}   body: { body?, company_id? }  → 200 Note
DELETE /notes/{note_id}   → 204
```

## Sources
```
POST /narratives/{id}/sources
  body: { kind: 'url'|'sec_filing'|'pdf'|'text', url?: string, raw_text?: string }
  → 201 Source
  # url/sec_filing: backend fetches title + excerpt via providers/fetch.py (sync).
  # text: stores raw_text as excerpt, title optional.
  # Returns 502 with detail if the fetch fails; the source is not created.

GET    /narratives/{id}/sources   → 200 { items: [Source] }
DELETE /sources/{source_id}       → 204
```

`Source`: `{ id, narrative_id, kind, url, title, excerpt, created_at }`

## Companies
**Built bare-bones** (no search, no hydration — see [`06-build-plan.md`](06-build-plan.md)
Phase D). Companies are a shared/global cache; `GET /companies/{id}` returns the plain
`Company`, not the enriched `CompanyDetail`, until hydration lands.
```
# --- BUILT (bare-bones) ---
POST /narratives/{id}/companies
  body: { ticker: string, name?: string }             # ticker normalized upper-case
  → 201 Company                                        # get-or-creates the company, attaches
  # Idempotent: re-attaching the same ticker is a no-op. Does NOT hydrate.

GET  /narratives/{id}/companies
  → 200 [ Company ]                                    # companies attached to the narrative

DELETE /narratives/{id}/companies/{company_id}
  → 204                                               # detach (company row persists, shared)

GET  /companies/{id}
  → 200 Company                                        # bare company (no referenced_in yet)

# --- DEFERRED ---
GET  /companies/search?q=<ticker-or-name>              # needs a symbol index — Phase D-search
  → 200 { items: [ { ticker, name, exchange, id? } ] }

POST /companies/{id}/hydrate                            # fetch profile/fundamentals — Phase D
  → 200 CompanyDetail                                 # sets last_hydrated_at. 502 on provider fail.
```

`Company`: `{ id, ticker, name, exchange, sector, profile, fundamentals, last_hydrated_at,
created_at, updated_at }` (profile/fundamentals are null until hydrated).
`CompanyDetail` (deferred): `Company` + `referenced_in: [ { narrative_id, title } ]`.

## Agent (current-narrative assistance)
See [`04-agent.md`](04-agent.md) for behavior/prompts.
```
POST /narratives/{id}/agent/summarize-source
  body: { source_id: uuid }
  → 200 { summary: string }

POST /narratives/{id}/agent/draft-section
  body: { kind: 'bull'|'bear'|'catalyst'|'risk', instruction?: string }
  → 200 { proposals: [ { body: string, source_id?: uuid, event_date?: date } ] }
  # Proposals are NOT saved. Frontend renders them for accept/edit/reject; accepting calls
  # POST /narratives/{id}/items.

POST /narratives/{id}/agent/ask
  body: { question: string }
  → 200 { answer: string, citations: [ { source_id, quote } ] }
  # Answered only from attached material; refuses/says-so when out of scope.
```

## Narrative intake (the guided questionnaire)
Full design in [`03-narrative-intake.md`](03-narrative-intake.md). Summary of the contract:
```
POST /narratives/intake
  body: { kernel: { kind: 'text'|'url'|'tweet'|'document', raw_text?: string, url?: string } }
  → 201 IntakeState                                   # ingests kernel, returns round-1 questions

GET  /narratives/intake/{draft_id}
  → 200 IntakeState                                   # resume a draft

POST /narratives/intake/{draft_id}/answer
  body: { answers: [ Answer ], finish_now?: boolean }
  → 200 IntakeState                                   # next questions, OR proposal if done
  # finish_now=true: skip remaining questions, synthesize from what we have.

POST /narratives/intake/{draft_id}/finalize
  body: { proposal: Proposal }                        # the user-edited proposal
  → 201 { narrative_id: uuid }                         # promotes draft → real narrative

DELETE /narratives/intake/{draft_id}
  → 204                                               # abandon
```

`IntakeState`: `{ draft_id, status, kernel: {...}, round, questions: [Question]|null,
proposal: Proposal|null }`

`Question`, `Answer`, `Proposal` schemas: see [`03-narrative-intake.md`](03-narrative-intake.md) §4.

---

## CORS & versioning
- CORS allows the frontend origin(s) only.
- Prefix all routes with `/api` (or `/api/v1` if we want headroom). Omitted above for brevity.

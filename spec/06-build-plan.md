# 06 — Build Plan

This extends the prep-notes roadmap (`v2/04-mvp-roadmap.md`) with concrete deliverables and
slots in the **guided intake questionnaire** (Phase G) and the **per-user memory system**
(Phase H) as their own phases. Same discipline: backend in small, reviewable Python
increments (each is one digestible PR with a test and a Python concept to learn); frontend a
step or two behind.

> **Learning-first reminder.** Tamara is also how we're learning Python. Keep each step
> small enough to fully read, run, and discuss; write/extend a test; then talk through the
> tagged Python concept *before* starting the next step. Resist batching steps together — the
> small-step rhythm is the point, not overhead.

**Ordering rules (unchanged):** equities only · everything user-initiated · no
background/auto work · Twitter ingestion is the last item.

Phases A–F mirror the prep notes; **Phase G (intake)** is new and sequenced after the agent
exists. Phase 0 covers project setup including the Supabase MCP.

---

## Build log & resequencing (live)

The plan below is the original target order. Actual building has resequenced a few things —
recorded here so the plan reflects reality:

- ✅ **Done:** Phase 0 (setup, Supabase project, MCP), Phase A (config, Supabase client + DI,
  local JWT auth via JWKS/ES256), Phase B (narratives CRUD + pytest), **C1** (section items),
  **C2** (notes), and **D1-lite** (bare-bones companies — see below).
- ⏸️ **Tabled for later:** **C3 / C4 (sources + citing a source from an item).** Deferred so we
  can stand up a frontend sooner. The `source_id` column on `narrative_items` and the
  `company_id` column on `notes` remain deferred until their parent features land.
- 🔀 **Pulled forward:** a **bare-bones companies** slice (attach/list/detach/get + the
  `companies` and `narrative_companies` tables) is built *before* the frontend, so the
  frontend has the full narrative shape (companies included) to render.
- ➡️ **Next:** the **frontend** (Phase FE-core below) — get a basic UI talking to the backend,
  then reassess priorities (sources, hydration, agent, intake) based on what the UI surfaces.
- 🔭 **Deferred within Phase D:** company **search / index** and **data hydration** (prices,
  fundamentals, profiles for companies/tickers/assets) are explicitly later work, not part of
  the bare-bones companies slice.

---

## Phase 0 — Setup & tooling
- **0.1 Repos & envs.** `backend/` (venv + `uv`/`requirements.txt`, `.env`) and `frontend/`
  (Vite + TS). Hello-world FastAPI route under `uvicorn`; Vite dev server.
- **0.2 Supabase project + Auth.** Create the project; enable Auth; note URL + keys.
- **0.3 Connect the Supabase MCP.** Wire the Supabase MCP into the dev environment and use it
  going forward for schema migrations, inspection, ad-hoc queries, type generation, and RLS
  verification (see [`01-architecture-and-data-model.md`](01-architecture-and-data-model.md)
  §3). **Rule:** every schema change the MCP applies is also captured as a committed file in
  `backend/migrations/` — the MCP is how we apply/inspect, not where the schema lives.
- **0.4 `config.py`.** Pydantic `BaseSettings` for all secrets/keys.
  *Learn:* venvs, project layout, typed settings, secret hygiene.

## Phase A — Backend foundations
- **A1 Supabase client + DI.** `db.py`; `/health` route doing one trivial query via
  `Depends`.
- **A2 Auth dependency.** `get_current_user` validates the Supabase JWT, extracts `user_id`.
  Written **once**, provider-agnostic — it never changes when we add auth methods later. Use
  the simplest working login during development (email OTP / a dev login); **do not get stuck
  on auth.** The polished two-method UX is deferred (see F0). Key all app state on `user_id`,
  never on email/handle.
- **A3 Pydantic models.** `models.py` — start with `Narrative` request/response.
- **A4 Schema & RLS (via MCP, mirrored to migration).** Create `narratives` + RLS owner
  policy. Verify RLS with the MCP (query as two users).
  *Learn:* Pydantic, FastAPI DI, SQL DDL, row-level security, the DB↔model boundary.

## Phase B — Narratives CRUD (establish the layering)
- **B1** `GET /narratives`, `GET /narratives/{id}` (router → service → db).
- **B2** `POST /narratives` (the blank-form path).
- **B3** `PATCH` / `DELETE`.
- **B4** Wire auth into all queries; scope to `user_id`; 404-not-leak behavior.
- **B5** `pytest` over the endpoints (happy path + auth + not-found).
- **FE-1 (parallel):** Vite app scaffold, Supabase login, Narratives list + "Start blank".
  *Learn:* routers vs services, async, validation, status codes, testing FastAPI, auth boundary.

## Phase C — The narrative's pieces
- ✅ **C1** `narrative_items` (bull/bear/catalyst/risk): table + RLS-via-parent + CRUD +
  reorder + optional `event_date`. **Done.**
- ✅ **C2** `notes`: table + CRUD scoped to a narrative (owner RLS). **Done.** (`company_id`
  on notes deferred until companies hydration matters.)
- ⏸️ **C3 — TABLED** `sources` (manual add): table + `providers/fetch.py` (URL GET → title +
  excerpt, timeouts/failures handled) + add-by-URL and add-as-text. *Deferred until after the
  first frontend.* This is the first **external-I/O / `providers/`** work.
- ⏸️ **C4 — TABLED** Cite a source from an item (`narrative_items.source_id` FK). Depends on
  C3; the `source_id` column is not added until then.
- **FE-2 (parallel):** Narrative view — four `SectionEditor`s, Notes panel, Sources panel,
  citation picker.
  *Learn:* enums/one-table-with-a-kind, DRY pattern reuse, `httpx`/HTML parsing, FKs.

## Phase D — Companies & Company view
> Split into a **bare-bones slice (done, built before the frontend)** and the **heavier data
> work (deferred)**.

- ✅ **D1-lite (done)** — bare-bones companies: `companies` (global, shared) +
  `narrative_companies` join tables; attach-by-ticker (get-or-create, ticker normalized),
  list, detach, and `GET /companies/{id}`. Companies RLS: `to authenticated` read + insert
  (a shared cache; tighten to service-role writes when hydration lands). **No search, no
  hydration.** *Learned:* many-to-many, shared-data (non-per-user) RLS, get-or-create,
  idempotent attach.
- 🔭 **D1-search (deferred)** `/companies/search` + a symbol **index** (Wikipedia S&P 500 list,
  ticker normalization). The searchable-company function.
- 🔭 **D2 (deferred)** `providers/edgar.py` via `edgartools` (≤8 req/s throttle, contact-info
  User-Agent); resolve ticker → profile + latest fundamentals.
- 🔭 **D3 (deferred)** `POST /companies/{id}/hydrate` → fetch, store snapshot, set
  `last_hydrated_at` (+ `providers/yfin.py` gap-fill, dev-only). **Hydration of company /
  ticker / asset data.** Likely introduces the **service-role** Supabase client for shared
  writes.
- 🔭 **D4 (deferred)** `GET /companies/{id}` enriched with profile/fundamentals + a
  "referenced in" list of the user's narratives.
- 🔭 **D5 (deferred, optional)** `providers/market.py` (FMP) behind the same interface, *after*
  clearing a display license.
- **FE-3 (parallel):** Companies panel + Company view with Fetch-data/last-fetched control.
  *Learn:* wrapping a 3rd-party lib, rate limiting, jsonb, joins, the provider abstraction.

## Phase FE-core — First frontend ★ pulled forward (next)
> Goal: a basic React + TS app talking to the backend, so we can *see* the product and let
> what it surfaces drive the next backend priorities. See [`05-frontend.md`](05-frontend.md).

- **FE-0 Scaffold.** Vite + React + TS app under `frontend/`; a typed `lib/api.ts` fetch
  wrapper; Supabase Auth login (simplest working method) attaching the JWT.
- **FE-1 Narratives list + create**, wired to `GET/POST /narratives`.
- **FE-2 Narrative view** — title/thesis, the four section-item lists (CRUD + reorder), Notes
  panel, and Companies chips (attach/detach) — wired to the items/notes/companies endpoints.
- **FE-3 (thin) Company view** — show the bare-bones company (ticker/name); "hydrate" and
  "referenced in" arrive with Phase D's deferred work.
- **Then reassess:** with a working UI, decide what's most valuable next (sources, company
  hydration/search, the agent, or the intake questionnaire).

## Phase E — The agent (user-initiated assistance)
- **E1** `providers/llm/` — the **provider-agnostic LLM gateway**: an `LLMGateway` interface
  (ABC/`Protocol`) + a default Anthropic adapter + role→model routing from config (synthesis /
  fast / embedding), with retries and structured-output enforcement. Services import the
  interface, never a vendor SDK. Then `services/agent.py` + `agent/summarize-source`.
  *Learn:* ABCs/Protocols and dependency inversion (designing to an interface), config-driven
  routing, calling an LLM. **Don't vendor-lock** — adding a second provider later is just a new
  adapter.
- **E2** Context assembly from a narrative's sources/notes/companies (token budgeting,
  data/instruction separation, prompt-injection hygiene).
- **E3** `agent/draft-section` → proposals with citations (propose-then-confirm).
- **E4** `agent/ask` → grounded Q&A with citations; out-of-scope refusal.
- **FE-4 (parallel):** Agent side panel; render proposals with accept/edit/reject; Q&A with
  citation chips.
  *Learn:* calling an LLM, structured output, RAG-lite grounding, provenance enforcement.

## Phase G — Guided narrative intake (the questionnaire) ★ new
> Depends on: sources fetch (C3), company resolve (D1), the agent + structured output (E).
> This is the flagship creation path. Build it after the agent primitives exist.

- **G1 Draft table + ingest.** `narrative_drafts` table (+ RLS) via MCP/migration;
  `POST /narratives/intake` creates a draft and ingests the kernel (text/document direct;
  url via `providers/fetch.py`; tweet degrades to text until Phase F).
  *Learn:* modeling a multi-turn session as state, jsonb transcript design.
- **G2 Question generation.** `agent.propose_questions` (structured output `{ready,
  questions}`), bounded to `MAX_ROUNDS=3`, ≤4 questions/round, adaptive to the kernel.
  *Learn:* designing an LLM that decides *whether* to ask vs. proceed; schema-constrained output.
- **G3 Answer loop.** `POST /narratives/intake/{id}/answer` — append to transcript, decide
  next-questions vs. synthesize; `finish_now` shortcut.
  *Learn:* a small server-side state machine, idempotency.
- **G4 Synthesis.** `agent.synthesize_narrative` → `Proposal` (title, thesis, companies,
  bull/bear/catalyst/risk items with `cite`, open_questions, confidence). Provenance rules
  enforced (no invented tickers/financials/dates).
  *Learn:* structured synthesis, honest confidence, citation discipline.
- **G5 Finalize.** `POST /narratives/intake/{id}/finalize` — transactional promote: create
  narrative + kernel source + items (with citations) + company attaches + notes from
  open_questions; idempotent.
  *Learn:* multi-table transactional writes, mapping a draft to real entities.
- **G6 Tests.** Intake flow tests: rich-kernel-skips-questions, bare-kernel-asks-more,
  skip-everything-low-confidence, finalize-idempotency, ticker-not-found path.
- **FE-G (parallel):** the three-step intake UI (Kernel / Question / Proposal), resumable by
  `:draftId`; make "Start from a kernel" the default New-narrative path.

## Phase H — Per-user agentic memory ★ new
> Depends on: the agent + structured output (E); benefits intake (G). Build the lightweight,
> user-confirmed slice; defer background distillation and embeddings (post-MVP). See
> [`07-user-memory.md`](07-user-memory.md).

- **H1 Memory table + management CRUD.** `user_memories` table (+ RLS) via MCP/migration;
  `GET/POST/PATCH/DELETE /memories` and the "What Tamara remembers" screen.
  *Learn:* modeling a per-user knowledge store, reusing the layered CRUD pattern once more.
- **H2 Recall + ranking (no embeddings).** `services/memory.py: recall()` —
  salience×recency×keyword-overlap ranking; always-include preferences/feedback; top-K within
  a token budget. Wire into `services/agent.py` context assembly; bump `use_count`/`last_used_at`.
  *Learn:* writing a ranking/scoring function, weighting, sorting, token budgeting.
- **H3 Agent-proposed memories (distillation).** `propose_memories()` structured-output call
  at the end of an interaction → candidates; `POST /memories/proposals/confirm` to persist
  accepted ones; supersession/merge on conflict. Propose-then-confirm; synchronous (no timer).
  *Learn:* structured LLM output again, conflict/supersession logic, the trust contract.
- **H4 Memory in intake.** Feed recalled `preference` memories into `propose_questions` so the
  questionnaire *confirms* known defaults instead of re-asking.
  *Learn:* composing two services (memory + intake) cleanly.
- **H5 (optional, can defer) Embeddings.** Enable `pgvector`; add `embedding` + cosine
  similarity to `recall()` behind the same ranking function.
  *Learn:* embeddings, vector indexes, swapping a strategy without touching callers.
- **FE-H (parallel):** the memory management screen; the "want me to remember…?" confirm UI
  rendered after intake/agent interactions.

## Phase F — Twitter ingestion + final auth (LAST, manual only)
- **F0 Two-method login + identity linking.** Now that we're standing up an X developer app
  for ingestion, wire the real `/login`: **email login code** (Supabase email OTP) and **Sign
  in with Twitter/X** (Supabase OAuth). Add the **Account settings** screen
  (`/settings/account`) so a user who signed up with email can **link their Twitter/X account
  to the same `user_id`** via `linkIdentity` (enable manual linking in Supabase; rely on
  manual link-while-authenticated since X usually returns no email). Backend is unchanged
  (`get_current_user` already provider-agnostic; data is keyed on `user_id`, so linking needs
  no migration). Deferred to here on purpose so auth never blocked the MVP.
  *Learn:* OAuth providers, the identity-vs-user distinction, why keying on a stable id pays off.
- **F1** `providers/twitter.py` resolves a tweet URL → author + text (graceful degradation).
- **F2** `POST /narratives/{id}/ingest-tweet` → create a `source` (`kind='tweet'`); optionally
  summarize via the agent. Also upgrades intake's `tweet` kernel path from text-degrade to a
  real resolve.
- **F3 (optional)** DM path, only if the X DM tier is affordable; else ship paste-only.
- **FE-5:** "Paste a tweet" on the narrative + as an intake kernel kind.
  *Learn:* working within strict API limits, composing existing services.

---

## MVP "done" definition
A user can: sign in → **create a narrative either by pasting a kernel and answering a short
guided questionnaire (which proposes a structured thesis they edit and accept) or from a
blank form** → attach companies and hydrate their data on request → add sources (incl. a
pasted tweet) and notes → write or have the agent draft the bull/bear/catalyst/risk sections
with citations → open a Company view to see its data and which narratives reference it →
**and Tamara remembers durable preferences/convictions about the user (confirmed, editable)
and uses them to personalize drafting and the intake questionnaire.** **All actions
user-initiated. Equities only.** Everything beyond → `v2/05-post-mvp.md`.

## Working rhythm (the learning goal)
- One backend step = one small PR, reviewed and discussed before the next.
- Each step: write it → run it → write/extend a test → talk through the Python concept.
- Use the Supabase MCP to apply/inspect schema and verify RLS as you go; commit the matching
  migration each time.
- Frontend phases trail their enabling endpoints. Resist pulling post-MVP ideas forward.

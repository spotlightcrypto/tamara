# 01 — Architecture & Data Model

## 1. Runtime shape

```
  React + TypeScript (Vite SPA)        FastAPI (Python)              Supabase (Postgres)
 ┌──────────────────────────┐  HTTPS  ┌──────────────────────┐  SQL ┌────────────────────┐
 │ Narrative view           │────────▶│ REST API (routers)   │─────▶│ tables + RLS       │
 │ Company view             │◀────────│ services (logic)     │      │ auth.users         │
 │ Intake questionnaire      │         │ providers (external) │      │ storage (post-MVP) │
 │ Agent chat panel         │         │ agent (Claude)       │      └────────────────────┘
 └──────────────────────────┘         └──────────┬───────────┘
       │ Supabase Auth (JWT)                     │ on user request only
       └─────────────────────▶ Supabase Auth     ├─▶ SEC EDGAR (edgartools)
                                                 ├─▶ price/fundamentals API (FMP, later)
                                                 ├─▶ yfinance (dev gap-fill only)
                                                 ├─▶ X/Twitter resolver (last MVP item)
                                                 └─▶ Anthropic Claude API (agent + intake)
```

- **Frontend** talks only to our FastAPI backend (except Supabase Auth for login). It never
  calls data providers or the LLM directly.
- **Backend** owns all business logic and every external call. **No background workers, no
  cron, no queues** in the MVP.
- **Supabase** provides Postgres + Auth. Row-Level Security scopes per-user data
  (narratives, notes, sources, drafts) to its owner. `companies` and fetched company data
  are a shared global cache, readable by all authenticated users.

### Auth model
- Supabase Auth issues a JWT to the frontend on login.
- The frontend sends `Authorization: Bearer <jwt>` on every API call.
- FastAPI validates the JWT (Supabase JWKS / shared secret), extracts `user_id` (the `sub`
  claim), and scopes all queries to it. Two enforcement layers, belt-and-suspenders:
  1. Service-layer `user_id` filtering on every per-user query.
  2. Postgres RLS policies as the backstop (see §4).

**Two intended sign-in methods — but deliberately deferred.** Production Tamara will offer:
1. **Email login code** — passwordless one-time code (Supabase email OTP).
2. **Twitter / X OAuth** — sign in with X (Supabase OAuth provider).

The important constraint: **do not get stuck on auth until most of the MVP is built.** Both
methods are just Supabase Auth providers, and — crucially — **the backend doesn't care which
method minted the JWT.** Supabase issues the same token shape regardless of provider, so
`get_current_user` (JWT → `user_id`) is written once and never changes; adding a method later
is mostly Supabase dashboard config plus a frontend button. Therefore:

- **Early/most of the MVP:** use the simplest thing that yields a real `user_id` — email OTP
  (trivial in Supabase) or a dev/test login. Build the whole app against that.
- **Late (near Phase F):** wire the real two-method login UX. **Twitter/X OAuth is naturally
  paired with the Twitter-ingestion feature (Phase F, the last MVP item)** — both need an X
  developer app and credentials, so set them up together rather than up front.

Design implication: keep everything keyed on the Supabase `user_id`, never on email or X
handle, so the auth method is swappable without touching data or business logic.

**One account, multiple identities (linking).** The two methods aren't separate accounts — a
user who signed up with email must be able to **add their Twitter/X login to the same
account** (and vice-versa) and then sign in either way. Supabase models this natively: one
`auth.users` row (one `user_id`) can have several rows in `auth.identities`, one per linked
provider. A logged-in user links X via `supabase.auth.linkIdentity({ provider: 'twitter' })`
(manual linking must be enabled in the Supabase dashboard); the `user_id` — and therefore all
their narratives, sources, memories — is unchanged.

Two caveats to design for:
- **X often returns no email**, so Supabase's *automatic* link-by-matching-email won't fire
  for Twitter. We rely on **manual linking while authenticated** (the user is logged in via
  email, then clicks "Connect Twitter/X"), which is the robust path anyway.
- Because we never key data on email/handle, linking is purely a Supabase Auth concern — **no
  app-side data migration** is needed when an identity is added. This is the third payoff of
  the `user_id`-only rule (the first two: swappable method, provider-agnostic backend).

This is part of the same deferred auth work (Phase F0) — but the data model already supports
it today, so nothing here blocks the MVP.

## 2. Repo layout

```
tamara/
  spec/                      # this spec
  backend/
    app/
      main.py                # FastAPI app, router registration, CORS
      config.py              # Pydantic BaseSettings (Supabase keys, provider keys, ANTHROPIC_API_KEY)
      db.py                  # Supabase client + JWT/user dependency (Depends(get_current_user))
      models.py              # Pydantic request/response schemas
      routers/
        narratives.py
        items.py             # bull/bear/catalyst/risk section items
        notes.py
        sources.py
        companies.py
        agent.py             # chat / draft / summarize / Q&A
        intake.py            # the guided narrative-intake questionnaire
      services/
        narratives.py
        items.py
        notes.py
        sources.py
        companies.py         # + hydration orchestration
        agent.py             # Claude calls: drafting, summarizing, Q&A
        intake.py            # intake state machine: ingest kernel, propose questions, synthesize
      providers/
        edgar.py             # SEC EDGAR via edgartools (UA + throttle)
        market.py            # price/fundamentals API (FMP) — added when needed
        yfin.py              # yfinance fallback (dev only)
        fetch.py             # generic URL fetch → title + excerpt
        twitter.py           # tweet resolver (last MVP item)
        llm/                 # provider-agnostic LLM gateway (NOT vendor-locked) — see 04-agent.md §1
          __init__.py        #   LLMGateway interface + get_llm(role) factory (services import this)
          registry.py        #   logical role -> provider:model routing, from config
          anthropic.py       #   Anthropic adapter (default provider)
          openai.py          #   another provider adapter, added when needed
          embeddings.py      #   embedding model abstraction (memory recall; provider-agnostic)
    migrations/              # SQL migration files (source of truth for schema)
    tests/                   # pytest
    pyproject.toml | requirements.txt
  frontend/
    src/
      routes/                # Narratives list, Narrative view, Company view, Intake
      components/
      lib/api.ts             # typed fetch wrapper, attaches JWT
      lib/supabase.ts        # Supabase Auth client
    package.json
```

**Layering rule:** routers do HTTP + validation only; services hold logic; providers wrap
external APIs. The intake feature follows the same layering (`routers/intake.py` →
`services/intake.py` → `services/agent.py` + `providers/fetch.py`/`twitter.py`).

## 3. Supabase MCP (developer tooling)

We will connect the **Supabase MCP server** and use it for a large share of database work
during development. Treat it as a *developer/agent-time* tool, not a request-path dependency:

- **Use it for:** authoring and applying migrations, inspecting schema, running ad-hoc and
  diagnostic queries, generating/refreshing TypeScript types from the live schema, seeding
  dev data, and verifying RLS policies behave as intended. When iterating on the data model
  below, prefer driving those changes through the Supabase MCP rather than hand-running SQL.
- **Do not** route production application traffic through the MCP. The running FastAPI app
  talks to Postgres via the Supabase client/`db.py` with the service or anon key as
  appropriate. The MCP is for build, migration, and inspection tasks.
- **Source of truth stays in `backend/migrations/`.** Anything the MCP applies to the
  database must be captured as a committed migration file so the schema is reproducible. The
  MCP is the convenient way to apply and check migrations, not a substitute for versioning
  them.
- **Credentials:** the MCP uses its own configured Supabase access token (a dev/admin
  scope), separate from the keys the app uses at runtime. Keep it out of the app's `.env`.

When this spec says "create table X / add policy Y," that work can be performed via the
Supabase MCP — and then mirrored into a migration file.

## 4. Data model (Postgres)

Deliberately few tables. The five core entities from the product spec, plus the intake
**draft** tables that power the questionnaire.

### 4.1 Core tables

```sql
-- narratives: the top-level thesis workspace (per-user)
create table narratives (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  title       text not null,
  thesis      text not null default '',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- companies: shared/global cache, hydrated on demand (NOT per-user)
create table companies (
  id               uuid primary key default gen_random_uuid(),
  ticker           text unique not null,        -- normalized, e.g. NVDA, BRK-B
  name             text not null,
  exchange         text,
  sector           text,
  profile          jsonb,                        -- description + provider profile blob
  fundamentals     jsonb,                        -- latest fetched financials snapshot
  last_hydrated_at timestamptz                   -- null = never fetched
);

-- narrative_companies: many-to-many narrative <-> company
create table narrative_companies (
  narrative_id uuid not null references narratives(id) on delete cascade,
  company_id   uuid not null references companies(id)  on delete cascade,
  primary key (narrative_id, company_id)
);

-- sources: a reference attached to a narrative (per-user)
create table sources (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  narrative_id uuid not null references narratives(id) on delete cascade,
  kind         text not null,                    -- 'url' | 'sec_filing' | 'pdf' | 'text' | 'tweet'
  url          text,                             -- null for kind='text'
  title        text,
  excerpt      text,                             -- fetched/extracted snippet
  created_at   timestamptz not null default now()
);

-- notes: free-text annotation (per-user), optionally tied to a company in the narrative
create table notes (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  narrative_id uuid not null references narratives(id) on delete cascade,
  company_id   uuid references companies(id) on delete set null,
  body         text not null,
  created_at   timestamptz not null default now()
);

-- narrative_items: the bull/bear/catalyst/risk points (one table, kind-discriminated)
create table narrative_items (
  id           uuid primary key default gen_random_uuid(),
  narrative_id uuid not null references narratives(id) on delete cascade,
  kind         text not null,                    -- 'bull' | 'bear' | 'catalyst' | 'risk'
  body         text not null,
  source_id    uuid references sources(id) on delete set null,  -- optional citation
  event_date   date,                             -- used by catalysts
  position     int not null default 0,           -- ordering within its section
  created_at   timestamptz not null default now()
);
```

### 4.2 Intake / draft tables (power the questionnaire)

A guided-intake session is a **draft narrative**: it holds the kernel, the running Q&A
transcript, and the agent's synthesized proposal. On accept, it is promoted into real
`narratives` + `narrative_items` + `sources` + `narrative_companies` rows. It is per-user
and short-lived; abandoned drafts can be GC'd later (no scheduler in MVP — a manual/lazy
cleanup is fine).

```sql
create table narrative_drafts (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  status        text not null default 'collecting',
                -- 'collecting' (asking questions) | 'proposed' (synthesis ready)
                -- | 'finalized' (promoted to a narrative) | 'abandoned'
  kernel_kind   text not null,                   -- 'text' | 'url' | 'tweet' | 'document'
  kernel_raw    text,                             -- pasted text / extracted document text
  kernel_url    text,
  kernel_title  text,                             -- fetched (url/tweet)
  kernel_excerpt text,                            -- fetched snippet
  round         int not null default 0,           -- how many question rounds asked
  transcript    jsonb not null default '[]'::jsonb, -- ordered turns: questions asked + answers given
  proposal      jsonb,                            -- synthesized draft (title, thesis, items, companies)
  narrative_id  uuid references narratives(id) on delete set null, -- set when finalized
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
```

`transcript` and `proposal` jsonb shapes are specified in
[`03-narrative-intake.md`](03-narrative-intake.md).

### 4.3 Indexes

```sql
create index on narratives        (user_id, updated_at desc);
create index on sources           (narrative_id);
create index on notes             (narrative_id);
create index on narrative_items   (narrative_id, kind, position);
create index on narrative_companies (company_id);     -- "referenced in" lookups
create index on narrative_drafts  (user_id, status, updated_at desc);
```

### 4.4 Row-Level Security

Enable RLS on every per-user table; `companies` and `narrative_companies` are shared.

```sql
alter table narratives       enable row level security;
alter table sources          enable row level security;
alter table notes            enable row level security;
alter table narrative_items  enable row level security;
alter table narrative_drafts enable row level security;

-- Per-user tables: owner-only. Example for narratives (repeat shape for sources, notes, drafts):
create policy narratives_owner on narratives
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- narrative_items has no user_id; gate via the parent narrative's ownership:
create policy items_via_parent on narrative_items
  for all using (
    exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
  ) with check (
    exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
  );

-- companies: shared read for any authenticated user; writes via backend service role only.
alter table companies enable row level security;
create policy companies_read on companies for select using (auth.role() = 'authenticated');
-- (no insert/update policy -> only the service-role key, used by the backend, may write)

-- narrative_companies: gate via the parent narrative.
alter table narrative_companies enable row level security;
create policy narr_companies_via_parent on narrative_companies
  for all using (
    exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
  ) with check (
    exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
  );
```

> RLS is the backstop. The backend also filters by `user_id` in the service layer, and uses
> the service-role key only for legitimately shared writes (company hydration). When the
> backend acts on behalf of a user, it should pass the user's JWT so `auth.uid()` resolves —
> or filter explicitly by the extracted `user_id`.

### 4.5 `updated_at` maintenance
Add a trigger (or set `updated_at = now()` in the service layer on every update) for
`narratives` and `narrative_drafts`. A trivial `set_updated_at()` trigger function is fine.

## 5. Configuration / secrets (`config.py`, Pydantic `BaseSettings`)

```
SUPABASE_URL
SUPABASE_ANON_KEY          # frontend-equivalent, for user-scoped calls
SUPABASE_SERVICE_ROLE_KEY  # backend-only, for shared company writes
SUPABASE_JWT_SECRET        # to validate incoming JWTs (or use JWKS URL)

# LLM — provider-agnostic. Configure keys for whichever providers you use:
ANTHROPIC_API_KEY          # default provider
OPENAI_API_KEY             # optional, if any role is routed to OpenAI
# Model routing by logical role -> "provider:model" (defaults live in config, env-overridable):
LLM_MODEL_SYNTHESIS        # e.g. anthropic:claude-opus-4-8   (drafting / intake synthesis)
LLM_MODEL_FAST             # e.g. anthropic:claude-haiku-4-5   (summarize / Q&A / question-gen)
LLM_MODEL_EMBEDDING        # e.g. openai:text-embedding-3-small (memory recall; when embeddings land)

EDGAR_USER_AGENT           # "Tamara michael@onspotlight.app" — required by SEC
FMP_API_KEY                # optional, added in D5/post-MVP
APP_ENV                    # dev | prod (gates yfinance fallback)
```

Never commit secrets. The Supabase MCP's access token is configured in the MCP client, not
in this `.env`.

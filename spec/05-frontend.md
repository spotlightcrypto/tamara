# 05 — Frontend (React + TypeScript)

Vite SPA, TypeScript throughout. Talks only to the FastAPI backend (plus Supabase Auth for
login). The comfortable side of the stack — built a step or two behind its enabling backend
endpoints.

## 1. Stack choices
- **Vite + React + TypeScript.**
- **Routing:** React Router.
- **Server state:** TanStack Query (caching, mutations, optimistic updates for item edits).
- **Auth:** `@supabase/supabase-js` for login/session; `lib/api.ts` attaches the JWT to every
  backend request and handles 401 → re-auth. **Two intended methods, deferred (see
  [`01-architecture-and-data-model.md`](01-architecture-and-data-model.md) auth note):**
  (1) **email login code** (Supabase email OTP) and (2) **Sign in with Twitter/X** (Supabase
  OAuth). Don't get stuck here — build most of the app behind the simplest working login
  (email OTP / dev login) and add the polished two-button `/login` screen late, pairing the
  X button with the Phase F Twitter work. Keep app state keyed on the Supabase `user_id`, not
  email or handle, so the method is swappable. An **Account settings** screen
  (`/settings/account`) lists linked identities and lets a logged-in user **connect
  Twitter/X** (`supabase.auth.linkIdentity({ provider: 'twitter' })`) or email to their
  existing account, and disconnect (keeping at least one). Same `user_id` throughout — no data
  migration.
- **Styling:** keep it light (Tailwind or CSS modules — implementer's call). No design system
  required for MVP.

## 2. Routes

```
/login                         Supabase Auth — see auth note below
/settings/account              Linked sign-in methods (connect/disconnect Twitter/X, email)
/                              Narratives list + "New narrative" entry
/narratives/new                Intake — kernel step (creates a draft, then routes to :id)
/narratives/new/:draftId       Intake — question + proposal steps (resumable)
/narratives/:id                Narrative view (primary workspace)
/companies/:id                 Company view
```

## 3. Key screens & components

### Narratives list (`/`)
- Cards: title, thesis snippet, company count, updated time.
- **New narrative** button → two choices: **Start from a kernel** (→ `/narratives/new`,
  the default) and **Start blank** (calls `POST /narratives`, routes straight to the view).

### Intake (`/narratives/new`, `/narratives/new/:draftId`)
The questionnaire UI. Three sub-steps driven by `IntakeState.status` + presence of
`questions`/`proposal` (see [`03-narrative-intake.md`](03-narrative-intake.md) §6):
- `KernelStep` — kind toggle (Text / Link / Tweet) + large input + submit. Shows a
  "reading your link…" state for url/tweet.
- `QuestionStep` — renders `Question[]` as `QuestionCard`s: prompt, single/multi option
  chips, a free-text field, per-card Skip. Footer: **Continue**, **Skip the rest &
  generate**, round indicator.
- `ProposalStep` — editable proposal: `title`/`thesis` inputs, `CompanyChips` (add via
  search / remove), four `SectionEditor`s with per-item add/edit/remove and a citation badge
  on kernel-cited items, `confidence` banner, `open_questions` toggle. Buttons: **Create
  narrative**, **Ask me a couple more**, **Regenerate**.
- Resumable via `:draftId` in the URL (`GET /narratives/intake/:id` on load). Abandon = `DELETE`.

Reusable: `QuestionCard` (option chips + free text) is the same primitive the agent chat
could later use for clarifying questions — build it generically.

### Narrative view (`/narratives/:id`)
- Header: editable `title` + `thesis`.
- Four `SectionEditor`s (Bull / Bear / Catalysts / Risks): ordered item lists, inline
  add/edit/remove, drag-or-button reorder (`items/{id}/move`), optional source citation
  picker per item, optional date on catalyst items.
- `CompaniesPanel`: chips → link to Company view; add via `/companies/search`.
- `NotesPanel`: list + add/edit free text.
- `SourcesPanel`: add by URL / paste text / (later) tweet; shows fetched title + excerpt.
- `AgentPanel` (side): chat input + actions — "summarize this source", "draft a bear case",
  "what am I missing?". Renders agent **proposals** with accept / edit / reject (accept →
  create-item mutation). Q&A answers render with citation chips linking to the source.

### Company view (`/companies/:id`)
- Profile (name, ticker, exchange, sector, description).
- Fundamentals/market block with a **Fetch data / last fetched** control
  (`POST /companies/:id/hydrate`) and a visible `last_hydrated_at` timestamp.
- **Referenced in**: the caller's narratives that include this company → click through.

## 4. Types
Generate/maintain TS types that mirror the API contracts (`Narrative`, `Item`, `Source`,
`Note`, `CompanyDetail`, `IntakeState`, `Question`, `Answer`, `Proposal`). Two viable
sources: hand-write them from [`02-api-contracts.md`](02-api-contracts.md), or generate from
the backend's OpenAPI schema (FastAPI emits one). Supabase MCP can also generate types from
the DB for any direct-table needs, but the app reads through the API, so API/OpenAPI types
are primary.

## 5. UX principles
- **Propose-then-confirm everywhere.** The agent and intake never mutate the user's data
  without an explicit accept.
- **Show provenance.** Cited items display their source; agent answers show citation chips.
- **Make "user-initiated" visible.** Hydration, fetching, and drafting have clear buttons and
  "last fetched / just now" feedback — nothing happens silently.
- **Fast path preserved.** Power users can always "Start blank" and hand-write.

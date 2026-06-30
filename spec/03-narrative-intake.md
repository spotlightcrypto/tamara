# 03 — Guided Narrative Intake (the questionnaire)

This is the flagship creation flow and the main addition over the prep notes. Instead of
starting a narrative from a blank title/thesis form, the user pastes a **kernel** — the seed
of a thesis — and an agentic flow asks a few smart, adaptive questions, then proposes a
fully-structured narrative the user edits and accepts.

It is **user-initiated and synchronous**: the user is sitting there answering questions. It
is not a background agent and does not violate the "no background jobs" guardrail. Each step
is one (sometimes two) Claude calls.

> **Core principle — narratives take a position.** Intake should sharpen a kernel into a
> **committed directional thesis** (a bet with a side), not a neutral both-sides summary.
> *Infer* the implied stance from the kernel and **dress it up** confidently; the synthesized
> thesis is the position, the bull case is foregrounded as THE case, and bear/risk are the
> *counter* (what breaks it), not equal-weight hedging. **Infer, don't fabricate** — never
> invent facts, tickers, or a stance the kernel doesn't support. The committed position is an
> editable default ("until indicated otherwise"); questions exist to *pin or establish* the
> position when the kernel is vague. (See the `narratives-take-a-position` design note.)

---

## 1. What the kernel can be

A kernel is anything that seeds a thesis:

| `kind`     | Input                                  | Ingestion in MVP |
|------------|----------------------------------------|------------------|
| `text`     | A pasted prompt or note ("AI datacenters are going to break the grid; long the nuclear names") | Used as-is. |
| `document` | Pasted long-form text (a memo, a research note) | Used as-is (paste text in MVP; file upload is post-MVP). |
| `url`      | A link to an article / blog post / filing | `providers/fetch.py` fetches title + excerpt (cleaned main text, truncated). |
| `tweet`    | A link to a tweet/thread               | `providers/twitter.py` resolves author + text. **Until Phase F lands, tweet kernels degrade to "paste the tweet text" (`kind='text'`).** |

If ingestion fails (dead link, paywall, fetch error), the flow degrades gracefully: it keeps
whatever was entered, tells the user the link couldn't be read, and lets them paste text
instead. It never blocks creation on a failed fetch.

The kernel text the agent works from is: `kernel_title` + `kernel_excerpt` (for url/tweet) or
`kernel_raw` (for text/document). On finalize, the kernel becomes the narrative's **first
Source** so drafted items can cite it.

---

## 2. End-to-end flow

```
 User clicks "New narrative → Start from a kernel"
        │
        ▼
 [Paste kernel]  ── POST /narratives/intake ─────────────────────────────────┐
        │                                                                     │
        ▼                                                                     ▼
 Backend: create narrative_drafts row (status='collecting'),         services/intake.py:
   ingest kernel (fetch/resolve if url/tweet),                         ingest_kernel()
   call agent.propose_questions(kernel, transcript=[], round=1)        propose_questions()
        │
        ▼
 Round 1 questions  ◀── IntakeState { questions: [...] }
        │
        ▼
 [User answers (or skips individual questions, or clicks "Generate now")]
        │  POST /narratives/intake/{id}/answer  { answers, finish_now? }
        ▼
 Backend: append answers to transcript; round += 1
   if finish_now OR round > MAX_ROUNDS OR agent says ready:
        → agent.synthesize_narrative(kernel, transcript)  → proposal
          status='proposed'; return IntakeState { proposal }
   else:
        → agent.propose_questions(...) → more questions; return IntakeState { questions }
        │
        ▼ (loop until proposed)
 [Proposal screen]  — editable: title, thesis, companies, bull/bear/catalyst/risk items
        │  user edits inline; can "Regenerate" or "Ask me more"
        ▼
 [Accept]  ── POST /narratives/intake/{id}/finalize { proposal } ──▶ creates:
        narratives row, narrative_items (with citations), sources (the kernel),
        narrative_companies (resolved tickers); status='finalized'
        → { narrative_id }  → redirect to the Narrative view
```

### Bounds (cost + UX governor)
- `MAX_ROUNDS = 3` question rounds. Each round asks **≤ 4 questions**.
- The agent may end early by setting `ready=true` when it has enough to synthesize a useful
  narrative — for a rich article kernel that's often after round 1.
- The user may end early at any point via `finish_now=true` ("Skip / generate now").
- Total Claude calls per narrative: typically 2–4 (1 per round + 1 synthesis). All
  user-initiated and synchronous.

---

## 3. What the questions are *for*

The questions exist to extract the handful of things that turn a vague seed into a
structured thesis. The agent is prompted to probe (adaptively — only what the kernel is
missing) for:

1. **The actual claim / direction.** What's the bet, and on what? (long/short, which names,
   which mechanism.)
2. **The companies.** Which tickers is this about? (Agent proposes candidates from the
   kernel; user confirms/adds. Resolution via `/companies/search`.)
3. **Time horizon.** Days, quarters, years? (Shapes catalysts vs. structural risks.)
4. **The strongest bull point** the user already believes.
5. **The thing that would break it** (seeds the bear case / risks).
6. **Known catalysts / dated events** (earnings, launches, decisions, unlocks-later).
7. **The user's edge / why now** — what they think the market is missing (sharpens the
   thesis summary; optional).

The agent does **not** ask all of these every time. A rich kernel (a detailed article) may
already answer 1–2 and 6; the agent then asks only the sharp, missing ones (e.g. "What's
*your* angle vs. the article's?" and "What's your horizon?"). A bare one-line prompt gets
more foundational questions. **It also skips what it already knows about the user**: recalled
`preference` memories (e.g. a usual 1–3 year horizon, bear-case-first style) turn a question
into a quick *confirm* instead of an ask — see [`07-user-memory.md`](07-user-memory.md) §5. Questions are phrased conversationally, each with a few
suggested options plus a free-text fallback so the user can answer fast or type freely.

---

## 4. Schemas

### 4.1 `Question` (returned to the frontend; mirrors a structured questionnaire)
```jsonc
{
  "id": "q_horizon",                 // stable within a draft
  "header": "Time horizon",          // short chip label (≤ ~16 chars)
  "question": "Over what time frame are you playing this thesis?",
  "options": [                        // 2–4 suggested answers
    { "label": "Months (this year)", "description": "Catalyst-driven, near-term" },
    { "label": "1–3 years",          "description": "Structural build-out" },
    { "label": "5+ years",           "description": "Long secular bet" }
  ],
  "multiSelect": false,               // true → user may pick several
  "allowFreeText": true               // always true: user can type their own answer
}
```

### 4.2 `Answer` (frontend → backend)
```jsonc
{
  "question_id": "q_horizon",
  "selected": ["1–3 years"],          // chosen option labels (empty if free-text only)
  "free_text": null,                   // user's typed answer, or null
  "skipped": false                     // true → user explicitly skipped
}
```

### 4.3 `transcript` (stored in `narrative_drafts.transcript`)
An ordered list of turns, so any round can be reconstructed and a draft resumed:
```jsonc
[
  { "round": 1, "questions": [ Question, ... ] },
  { "round": 1, "answers":   [ Answer, ... ] },
  { "round": 2, "questions": [ Question, ... ] },
  { "round": 2, "answers":   [ Answer, ... ] }
]
```

### 4.4 `Proposal` (synthesized draft; stored in `narrative_drafts.proposal`, edited on the
proposal screen, sent back on finalize)
```jsonc
{
  "title": "AI datacenter power crunch",
  "thesis": "Hyperscaler datacenter build-out is outrunning grid capacity; the cheapest...",
  "companies": [
    { "ticker": "VST",  "name": "Vistra",            "reason": "Merchant power, nuclear+gas fleet" },
    { "ticker": "CEG",  "name": "Constellation Energy","reason": "Largest US nuclear operator" },
    { "ticker": "NVDA", "name": "NVIDIA",             "reason": "Demand driver named in the kernel" }
  ],
  "items": [
    { "kind": "bull",     "body": "Datacenter load growth is structurally underpriced by utilities.", "cite": "kernel" },
    { "kind": "bull",     "body": "Nuclear PPAs with hyperscalers lock in premium pricing.",            "cite": null },
    { "kind": "bear",     "body": "Rate-case / regulatory pushback could cap merchant upside.",         "cite": null },
    { "kind": "catalyst", "body": "Q3 earnings + any new hyperscaler PPA announcements.",   "event_date": "2026-08-01", "cite": null },
    { "kind": "risk",     "body": "A demand air-pocket if AI capex pauses breaks the thesis.",          "cite": null }
  ],
  "open_questions": [                  // unanswered threads → become Notes on finalize (optional)
    "Confirm VST's exact nuclear MW vs. gas split."
  ],
  "confidence": "medium"              // agent's self-assessment; shown as a banner, drives how much is pre-filled
}
```

`cite` is a symbolic reference resolved at finalize time:
- `"kernel"` → the item cites the kernel Source (created during finalize).
- `null` → no citation (an inference / the user's own belief; not falsely attributed).

The agent must only set `cite: "kernel"` when the claim is actually supported by the kernel
text. Inferences and user-supplied beliefs get `cite: null`. (Provenance discipline from
[`04-agent.md`](04-agent.md).)

---

## 5. Backend state machine (`services/intake.py`)

```
POST /narratives/intake
  ├─ create narrative_drafts(user_id, status='collecting', kernel_kind, round=0)
  ├─ ingest_kernel():
  │     url   → providers/fetch.py   → kernel_title, kernel_excerpt   (on fail: flag, keep raw)
  │     tweet → providers/twitter.py → kernel_title, kernel_excerpt   (pre-Phase-F: treat as text)
  │     text/document → kernel_raw
  ├─ round = 1
  ├─ q = agent.propose_questions(kernel, transcript=[], round=1)
  ├─ append {round:1, questions:q} to transcript; persist
  └─ return IntakeState{ status:'collecting', round:1, questions:q }

POST /narratives/intake/{id}/answer  { answers, finish_now }
  ├─ load draft (404 if not owner)
  ├─ append {round, answers} to transcript
  ├─ ready = finish_now or draft.round >= MAX_ROUNDS
  ├─ if not ready:
  │     decision = agent.propose_questions(kernel, transcript, round+1)
  │     if decision.ready: ready = true
  │     else:
  │        round += 1; append {round, questions:decision.questions}; persist
  │        return IntakeState{ status:'collecting', round, questions:decision.questions }
  ├─ # ready → synthesize
  ├─ proposal = agent.synthesize_narrative(kernel, transcript)
  ├─ status='proposed'; store proposal; persist
  └─ return IntakeState{ status:'proposed', proposal }

POST /narratives/intake/{id}/finalize  { proposal }   # proposal = user-edited
  ├─ load draft (404 if not owner); require status in ('proposed','collecting')
  ├─ transaction:
  │   ├─ insert narratives(title, thesis) → narrative_id
  │   ├─ insert source for the kernel (kind from kernel_kind; url/excerpt/title) → kernel_source_id
  │   ├─ for each company in proposal.companies:
  │   │     resolve/create companies row by ticker (no hydration); insert narrative_companies
  │   ├─ for each item in proposal.items (preserve order → position):
  │   │     source_id = kernel_source_id if item.cite=='kernel' else null
  │   │     insert narrative_items(kind, body, source_id, event_date)
  │   ├─ for each open_question: insert a note (body, narrative_id)   # optional, if non-empty
  │   └─ update draft: status='finalized', narrative_id
  └─ return { narrative_id }
```

`agent.propose_questions` and `agent.synthesize_narrative` use Claude with **structured
output** (a forced tool/JSON schema) so the backend gets validated objects, not prose — see
[`04-agent.md`](04-agent.md) §3. Retries on schema-mismatch happen in `providers/llm.py`.

### Idempotency / safety
- `finalize` is guarded: if `status='finalized'` already, return the existing `narrative_id`
  (don't double-create).
- A draft with no answers and `finish_now=true` still synthesizes — best-effort from the
  kernel alone, `confidence: "low"`, fewer pre-filled items, more `open_questions`.

---

## 6. Frontend (intake UI)

A dedicated route `/narratives/new` with three steps (see [`05-frontend.md`](05-frontend.md)
for component detail):

1. **Kernel step** — a single large input with a kind toggle (Paste text / Link / Tweet) and
   a "What's the seed of your thesis?" prompt. Submitting calls `POST /narratives/intake`.
   Shows a small "reading your link…" state while the URL/tweet is fetched.
2. **Question step** — renders the current round's `Question[]` as cards: each shows the
   question, selectable option chips (single or multi), and a free-text field ("Or in your
   own words…"). Per-question **Skip**. Footer has **Continue** (submit answers → next round)
   and **Skip the rest & generate** (`finish_now=true`). A progress hint ("Round 1 of up to
   3"). Adaptive: the number/shape of cards changes per round.
3. **Proposal step** — the synthesized narrative, fully editable inline: title + thesis
   fields; company chips (remove / add via search); four section lists with add/edit/remove
   per item and a citation badge ("from your source") on `cite:"kernel"` items; the
   `confidence` banner; `open_questions` shown as "we'll save these as notes" (toggle off to
   drop). Buttons: **Create narrative** (`finalize`), **Ask me a couple more questions**
   (re-opens the question step), **Regenerate**.

Resumable: the draft id is in the URL (`/narratives/new/{draft_id}`); reloading calls
`GET /narratives/intake/{draft_id}` to restore state. Abandoning calls `DELETE`.

The **"Start blank"** option on the Narratives list still calls `POST /narratives` directly
and skips intake entirely — the questionnaire is the default but never mandatory.

---

## 7. Worked example

**Kernel (text):** "I keep seeing that AI datacenters are going to overwhelm the power grid.
I think the utilities and nuclear names are the way to play it."

**Round 1 questions (from kernel alone):**
- *Which names?* options: [Nuclear operators (CEG, VST) · Independent power (NRG) · Grid/T&D
  (GEV, ETN) · Not sure — suggest some] (multiSelect, free text)
- *Long or short, and the mechanism?* [Long power producers · Long picks-and-shovels · Pair
  trade · Other]
- *Horizon?* [Months · 1–3 years · 5+ years]
- *What would make you wrong?* (free-text-leaning)

**User answers:** nuclear operators + "not sure, suggest"; long power producers; 1–3 years;
"if AI capex slows."

**Round 2 (adaptive — agent now has direction, sharpens):**
- *Add NVDA as the demand driver to watch?* [Yes, as context · No, keep it to the utilities]
- *Any dated catalysts you're tracking?* [Next earnings · A specific PPA/announcement · None
  yet]

Agent sets `ready=true` after round 2 → **synthesize** → the `Proposal` in §4.4. User tweaks
two bullet points, removes NVDA, clicks **Create narrative**.

---

## 8. Edge cases & rules

- **No resolvable tickers:** propose companies by name with empty/uncertain ticker; the
  proposal screen forces the user to confirm via `/companies/search` before those chips are
  attachable. Never invent a ticker.
- **Kernel fetch fails:** flag on the kernel step, proceed with whatever text exists; if
  truly empty, require at least a sentence before starting.
- **User skips everything:** synthesize low-confidence; mark items clearly; lean on
  `open_questions`.
- **Hallucination guard:** synthesized factual claims must be traceable to the kernel or to a
  user answer; otherwise `cite:null` and phrased as a hypothesis, not a fact. The synthesis
  prompt forbids fabricating financials, dates, or quotes.
- **No hydration during intake:** attaching proposed companies does **not** fetch their data
  (keeps creation fast and on-guardrail). The user hydrates later from the Company view.
- **Privacy/cost:** drafts are per-user (RLS); abandoned drafts can be deleted by the user
  and lazily GC'd later (no scheduler in MVP).

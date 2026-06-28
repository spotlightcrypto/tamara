# 07 — Per-User Agentic Memory

Tamara is a **personal investment-research agent**, not just a CRUD app over narratives. For
the agent to feel personal and get better over time, it needs a **memory system that is
separate from the content tables** — durable knowledge *about the user and their thinking*
that doesn't belong to any single narrative.

The `narratives`/`items`/`sources`/`notes` tables hold **content** (the theses themselves).
Memory holds **cross-cutting knowledge about the user**: how they like to work, what they
believe, the entities and sectors they keep circling, the corrections they've given the
agent, and facts they've told it. This is the layer that lets the intake questionnaire ask
*fewer* questions, lets drafting match the user's voice, and lets Q&A reference what the user
concluded last month.

> This is a deliberate design pillar, but it is **scoped**: the MVP ships a lightweight,
> user-confirmed slice; the heavier "agent quietly distills everything in the background"
> version is post-MVP, because background distillation would break the **user-initiated
> only** guardrail. See §6 for the split.

---

## 1. Two layers of memory

1. **Working / episodic memory** — the current conversation and the narrative's attached
   material. Already assembled per request in `services/agent.py` (see
   [`04-agent.md`](04-agent.md) §4). Ephemeral; not persisted as "memory."
2. **Long-term / semantic memory** — a curated, per-user store of durable facts and
   preferences (`user_memories`), recalled into context on relevant agent calls. This doc is
   about layer 2.

The relationship mirrors how a good human analyst works: the conversation is what's in front
of them right now; the long-term memory is what they *know about this client* and bring to
every conversation without being re-told.

---

## 2. What gets remembered (memory types)

| `type`        | What it captures | Example |
|---------------|------------------|---------|
| `preference`  | How the user wants the agent to work; their defaults | "Default horizon 1–3 years." "Show the bear case first." "Don't hedge — be direct." |
| `conviction`  | Durable views the user holds | "Structurally bullish on grid/nuclear power." "Skeptical of unprofitable growth names." |
| `entity`      | Companies/sectors/people the user repeatedly engages, plus their stance | "Watches VST, CEG closely." "Avoids Chinese ADRs." |
| `feedback`    | Corrections the user gave the agent, with the *why* | "Over-cited last time — one citation per claim is enough." |
| `fact`        | A personal fact the user told the agent, not captured in any table | "Is a PM focused on US utilities." (PII/compliance-sensitive — see §7) |
| `insight`     | Cross-narrative observations the agent surfaced and the user kept | "Three of your narratives all depend on AI-capex continuing." |

`insight`/cross-narrative memory is the lightweight precursor to the post-MVP
"cross-narrative intelligence" lens (`v2/05-post-mvp.md` §6) — same idea, captured as a
single confirmed memory instead of a background graph.

---

## 3. Data model

A single per-user table, RLS-scoped to its owner (never shared across users — unlike the
global `companies` cache).

```sql
create table user_memories (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  type          text not null,        -- preference|conviction|entity|feedback|fact|insight
  title         text not null,        -- short label, for the management UI and quick scan
  body          text not null,        -- the memory itself; for feedback/conviction include the "why"
  source        text not null,        -- 'user_stated' | 'agent_proposed' (confirmed by user)
  salience      int  not null default 3,    -- 1..5 importance, drives recall ranking + pruning
  status        text not null default 'active', -- active | archived | superseded
  superseded_by uuid references user_memories(id),
  related_narrative_id uuid references narratives(id) on delete set null,
  related_company_id   uuid references companies(id)  on delete set null,
  -- recall signals
  last_used_at  timestamptz,
  use_count     int not null default 0,
  -- semantic recall (added when we introduce embeddings; see build plan)
  embedding     vector(1536),         -- pgvector; nullable until embeddings land. Dimension is
                                       -- tied to the chosen embedding model (via the LLM gateway's
                                       -- 'embedding' role). Switching embedding providers/models
                                       -- changes the dimension and requires re-embedding all rows.
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index on user_memories (user_id, status, type);
create index on user_memories (user_id, salience desc, last_used_at desc nulls last);
-- when embeddings land:
-- create index on user_memories using ivfflat (embedding vector_cosine_ops);
```

RLS: owner-only (same shape as `narratives`). `pgvector` is a Supabase extension enabled when
embeddings are introduced — not required for the first cut (see §5/§6).

---

## 4. Writing memory (the agentic part) — propose-then-confirm

Memory is written two ways, and in the MVP **both are confirmed by the user** — nothing is
silently learned:

1. **Explicit.** The user says "remember that I…" (or edits memory directly in the management
   UI). Stored immediately, `source='user_stated'`.
2. **Agent-proposed.** At the end of a meaningful interaction (a finished intake, an accepted
   draft, a chat where the user corrected the agent), the agent may **propose candidate
   memories**: "I noticed you keep coming back to grid/power names and prefer a 1–3 year
   horizon — want me to remember those?" The user accepts / edits / declines. Accepted →
   `source='agent_proposed'`.

This keeps memory on the same trust contract as everything else: **the agent proposes, the
user confirms.** It also keeps us inside the no-background-jobs guardrail — distillation runs
synchronously at the end of a user action, not on a timer.

### Conflict & supersession
When a new memory contradicts an existing one (e.g. horizon changed from "1–3 years" to
"months"), the agent proposes marking the old one `status='superseded'` (`superseded_by` →
new id) rather than silently overwriting. The user sees and confirms the change. Duplicates
are merged the same way.

### Distillation operation
`services/memory.py: propose_memories(interaction_context) -> [CandidateMemory]` — a
structured-output Claude call (schema-constrained, like the rest of the agent) that reads the
just-finished interaction + existing memories and returns candidate writes/supersessions with
type, title, body, salience, and a one-line rationale. The router returns these as proposals;
a confirm endpoint persists the accepted ones.

---

## 5. Recalling memory (into agent context)

On every agent call (chat, draft-section, Q&A, **and intake**), `services/agent.py` pulls a
small, ranked set of memories into context alongside the narrative material:

- **Always include** high-salience `preference` and active `feedback` memories (they govern
  *how* to respond — small in number, cheap to always carry).
- **Relevance-rank** the rest and take top-K within a token budget. Ranking:
  `score = w1·salience + w2·recency(last_used_at) + w3·relevance(current context)`.
  - **First cut (no embeddings):** `relevance` = keyword/tag overlap with the current
    narrative's title/companies + `related_*` matches. Simple, debuggable, good Python
    practice (ranking, weighting, sorting).
  - **Later:** `relevance` = cosine similarity via pgvector between the memory `embedding` and
    an embedding of the current context. Drop-in upgrade behind the same ranking function. The
    embedding model is obtained through the LLM gateway's `embedding` role
    ([`04-agent.md`](04-agent.md) §1), so it's provider-agnostic too — just mind that changing
    embedding models means re-embedding existing rows (the vector dimension changes).
- On use, bump `use_count` and `last_used_at` (feeds future ranking and pruning).

Memories enter the prompt in a clearly delimited, **read-as-context-not-instructions** block
(prompt-injection hygiene — a memory is data about the user, not a command), and the agent is
told these reflect prior sessions and may be stale.

### Memory makes intake smarter
During the guided questionnaire ([`03-narrative-intake.md`](03-narrative-intake.md)), recalled
preferences let `propose_questions` **skip what it already knows** and instead *confirm*:
"I'll assume your usual 1–3 year horizon and bear-case-first style — change either?" This is
the most visible payoff of the memory system and a good demo of the layers working together.

---

## 6. MVP slice vs. post-MVP

**MVP (lightweight, on-guardrail):**
- `user_memories` table + RLS.
- Explicit "remember this" + **end-of-interaction agent-proposed** memories (confirmed).
- Recall into agent + intake context with **simple ranking (no embeddings yet)**.
- A **"What Tamara remembers about you"** management screen: list by type, edit, delete,
  archive. Essential for trust.

**Post-MVP (needs background infra or more depth — deferred with the rest of §1 in
`v2/05-post-mvp.md`):**
- **Background distillation** — passively mining sessions/filings/news for memories on a
  cadence (needs workers; breaks no-background-jobs until then).
- **Embeddings + pgvector** semantic recall (can be pulled forward if simple ranking proves
  too blunt — it's a contained upgrade).
- **Automatic decay/pruning** of stale, low-salience memories.
- **Cross-narrative `insight` mining at scale** — the connection/knowledge-graph lens.
- **Memory-driven proactivity** — "you said you'd revisit if X; X happened."

---

## 7. Trust, privacy & compliance

A personal agent that remembers you must be **transparent and user-controlled** — doubly so in
an investment context:

- **User-visible & editable.** Everything the agent remembers is shown in the management
  screen; the user can edit or delete any memory at any time. No hidden memory.
- **Per-user isolation.** Memories are RLS-scoped and **never** shared across users or folded
  into the global `companies` cache.
- **PII / sensitive facts.** Be conservative with `fact` memories — avoid storing sensitive
  personal/financial details unless the user explicitly asks; surface what's stored.
- **Not advice.** Memory personalizes *the research workspace*; it must not drift into
  unlicensed personalized investment advice. Same compliance posture as the rest of Tamara.
- **Deletion.** Deleting a user (or a narrative) cascades/cleans related memories
  appropriately (`on delete cascade` / `set null` as in the DDL).

---

## 8. Where it lives in the code

```
backend/app/
  routers/memory.py     # list / create / update / delete; propose; confirm-proposed
  services/memory.py    # write (explicit + distillation), recall/ranking, supersession
  models.py             # Memory, CandidateMemory, MemoryProposal schemas
```

`services/agent.py` and `services/intake.py` both call `services/memory.py: recall(...)` when
assembling context, and call `propose_memories(...)` at the end of an interaction. Memory is
just another service behind the same layering — and another clean Python learning slice
(ranking functions, later embeddings/pgvector, supersession logic).

API sketch (full contracts go in [`02-api-contracts.md`](02-api-contracts.md) when built):
```
GET    /memories                       → { items: [Memory] }            # the management screen
POST   /memories       { type, title, body, salience? }                 # explicit "remember this"
PATCH  /memories/{id}  { ...editable } ; DELETE /memories/{id}
POST   /memories/proposals/confirm     { accept: [Candidate], reject: [id] }  # after a distillation
```
(Distillation itself is invoked internally at the end of intake/agent interactions, returning
candidates the frontend renders for confirm/decline.)

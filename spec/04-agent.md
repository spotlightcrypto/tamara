# 04 — The Agent (LLM integration)

One assistant, scoped to a single narrative (or, during creation, to a draft). It helps the
user **on request** and never runs on its own. Everything it asserts as fact must be
traceable to attached material or a user statement.

## 1. Model & client — provider-agnostic by design

**We may use multiple AI models/providers; the architecture must not be locked into
Anthropic.** Services never import a vendor SDK or hardcode a model id — they depend on a
small **LLM gateway** abstraction. Swapping a model or provider is a config change, not a code
change.

```
providers/llm/
  __init__.py     # LLMGateway interface + get_llm(role) factory; this is what services import
  registry.py     # role -> (provider, model) routing, read from config (env-overridable)
  anthropic.py    # Anthropic adapter (default)
  openai.py       # OpenAI adapter (add when/if needed)
  embeddings.py   # embedding model abstraction (for memory recall; also provider-agnostic)
```

- **`LLMGateway` interface** (Python ABC / `Protocol` — itself a nice learning topic:
  dependency inversion): a couple of normalized methods, e.g.
  `complete(messages, *, role) -> str` and
  `structured(messages, schema, *, role) -> dict`. Adapters implement these per provider; the
  gateway normalizes the differences (Anthropic tool-use vs. OpenAI JSON-schema/function
  calling, message formats, token accounting).
- **Model routing by *role*, not by name.** Callers ask for a logical role; the registry maps
  it to a concrete `provider:model` from config:
  - `synthesis` — drafting / intake synthesis (quality-first; low volume, user-initiated).
  - `fast` — summarization / Q&A / intake question-generation (cheaper/faster tier).
  - `embedding` — memory recall vectors (post-MVP / when embeddings land).
  This is the clean home for "cheaper model tiering" from the prep notes — and lets us route
  different tasks to different vendors.
- **Defaults, not lock-in.** A sensible default config uses the latest Claude (e.g. an Opus
  tier for `synthesis`, a Haiku/Sonnet tier for `fast`) — they're strong defaults and we're an
  Anthropic-friendly shop — but any role can be pointed at another provider via config. Verify
  current Claude model ids/pricing via the `claude-api` skill; verify other providers against
  their own docs.
- **Gateway responsibilities (provider-independent):** role→model routing, timeouts, retries
  with backoff, **structured-output enforcement** (force schema-constrained output and
  re-prompt on validation failure — see §3), token-budget guarding, and per-call usage/cost
  logging (so we can compare models). Optionally we can sit this on top of a multi-provider
  library (e.g. LiteLLM) instead of hand-rolling every adapter — but the *interface stays
  ours*, so services are insulated either way.

## 2. Capabilities (MVP)

All triggered by an explicit user action; all scoped to one narrative's attached material +
the configured data providers. The agent does **not** freely browse the web in the MVP.

| Capability | Endpoint | Output contract |
|---|---|---|
| Summarize a source | `agent/summarize-source` | `{ summary }` |
| Draft a section | `agent/draft-section` | `{ proposals: [{body, source_id?, event_date?}] }` — **not saved**; propose-then-confirm |
| Q&A over the narrative | `agent/ask` | `{ answer, citations: [{source_id, quote}] }` — answered only from attached material |
| Generate intake questions | (internal, used by `services/intake.py`) | `{ ready, questions: [Question] }` |
| Synthesize a narrative | (internal, used by `services/intake.py`) | `Proposal` (see intake §4.4) |

## 3. Structured output

For everything except free-form summaries, the agent returns **validated JSON**, not prose.
Implementation: define a JSON Schema per operation and ask the **gateway** for
schema-constrained output. Each provider adapter uses that vendor's native mechanism
(Anthropic tool-use, OpenAI JSON-schema/function calling, etc.) to honor the same schema; the
gateway validates and re-prompts up to N times on mismatch, then surfaces a clean error to the
service. The **service layer sees only the validated dict** — it never knows which provider or
mechanism produced it, which is exactly what keeps us provider-agnostic and parsing-free.

Operations with schemas:
- `propose_questions` → `{ ready: boolean, rationale: string, questions: Question[] }`
  (`questions` empty when `ready`).
- `synthesize_narrative` → `Proposal`.
- `draft_section` → `{ proposals: DraftItem[] }`.
- `answer_question` → `{ answer: string, citations: Citation[], out_of_scope: boolean }`.

## 4. Context assembly (`services/agent.py`)

For a given narrative, build the prompt context from its attached material:
- Narrative `title` + `thesis`.
- The four section item lists (so drafts don't duplicate existing points).
- Attached `sources` (title + excerpt; full text only if small enough for the token budget).
- `notes`.
- Attached `companies` (ticker + name + last hydrated profile/fundamentals **if present** —
  never trigger a hydration just to answer; use what's cached).

Plus **recalled user memories** — a small, ranked set of durable facts/preferences about the
user from the per-user memory store (always-include preferences/feedback + top-K relevant
others). See [`07-user-memory.md`](07-user-memory.md) §5; `services/agent.py` calls
`services/memory.py: recall(...)` during context assembly and `propose_memories(...)` at the
end of an interaction.

Rules baked into context assembly:
- **Separate data from instructions.** System/instruction text says what to do; a clearly
  delimited data block carries the user's material. Treat attached source/note text as
  untrusted content, not instructions (prompt-injection hygiene).
- **Token budgeting.** Rank/truncate excerpts to fit; tell the model when material was
  truncated so it doesn't over-claim completeness.
- For **intake**, the "context" is the kernel + the Q&A transcript instead of a saved
  narrative.

## 5. Provenance (non-negotiable)

- Every **factual** claim the agent drafts must cite a source the user has attached (or, in
  intake, the kernel / a user answer). The drafting/synthesis schemas carry a `source_id` /
  `cite` field for this.
- When the agent makes an inference or states the user's own belief, it sets the citation to
  `null` and phrases it as a hypothesis — it does **not** fabricate a source.
- The agent must **never invent** financials, dates, tickers, or quotes. If it doesn't have
  the fact, it says so (Q&A: `out_of_scope:true`; drafting: omit or mark as a question).
- Q&A answers come **only** from attached material. Out-of-scope questions return
  `out_of_scope:true` and a short "not in your attached sources" message rather than a
  guessed answer.

## 6. Propose-then-confirm

The agent never writes to the user's narrative directly. `draft-section` and intake
synthesis return **proposals**; the frontend renders them for accept / edit / reject; only an
explicit user accept calls the create endpoints (`POST .../items`, intake `finalize`). This
is the core trust contract of the MVP.

## 7. Prompt sketches (starting points, refine in build)

**`propose_questions` (intake):** system role = "You are helping an investor turn a rough
thesis kernel into a structured narrative. Given the kernel and the conversation so far,
decide whether you have enough to draft a useful narrative. If not, ask up to 4 sharp,
*non-redundant* questions targeting only what's missing among: the specific claim/direction,
which companies/tickers, time horizon, strongest bull point, what would break it, dated
catalysts, the user's edge. Prefer offering 2–4 concrete options per question plus room for a
free-text answer. Never ask what the kernel already answers." Output schema = `{ready,
rationale, questions}`.

**`synthesize_narrative` (intake):** "Using the kernel and the answers, produce a structured
narrative: a concise title; a 2–4 sentence thesis in the user's framing; the companies
(tickers when known, else name + reason — never invent a ticker); and initial bull/bear/
catalyst/risk items. Cite the kernel (`cite:"kernel"`) only for claims actually supported by
its text; everything else `cite:null`. Do not fabricate financials, dates, or quotes. Put
genuinely-open threads in `open_questions`. Set `confidence` honestly." Output schema =
`Proposal`.

**`draft_section`:** "Draft {kind} points for this narrative from the attached sources only.
Each point: one or two sentences, citing the `source_id` it came from. Don't duplicate
existing points. If the sources don't support a {kind}, return fewer (or zero) rather than
inventing." Output schema = `{proposals}`.

> These are sketches. Iterate against real kernels during Phase E/G and keep the schemas as
> the contract.

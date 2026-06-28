# Tamara — Implementation Spec

This is the **buildable** spec: concrete data model, API contracts, the guided
narrative-intake questionnaire, the agent design, the frontend breakdown, and a sequenced
build plan. It turns the v2 preparation notes into something an engineer can implement
directly.

It builds on (and does not replace) the v2 prep notes in
`ai-notepad/tamara/v2/`:

- `v2/01-product-spec.md` — what Tamara is (narratives, companies, notes, sources, four
  sections) and the MVP guardrails.
- `v2/02-architecture.md` — stack and shape (React + FastAPI + Supabase).
- `v2/03-data-sources.md` — equities data landscape and the redistribution/licensing gate.
- `v2/04-mvp-roadmap.md` — the incremental, Python-learning build order.
- `v2/05-post-mvp.md` — everything deferred.

Where this spec and the notes disagree, **this spec wins** for implementation detail; the
notes win for product intent and scope discipline.

## What's new vs. the prep notes

Two additions sit on top of the v2 notes:

1. A **guided intake questionnaire** as the primary narrative-creation path: the user pastes
   a *kernel* (a prompt, a document, an article/tweet link), and an agentic flow asks a few
   smart, adaptive questions, then proposes a fully-structured narrative to edit and accept.
   The blank-form path still exists as "Start blank." See
   [`03-narrative-intake.md`](03-narrative-intake.md).
2. A **per-user agentic memory system** (`07-user-memory.md`): Tamara is a *personal* agent,
   so beyond the content tables it keeps durable, cross-cutting knowledge about each user —
   their preferences, convictions, the entities they circle, and corrections they've given —
   recalled into the agent and the intake questionnaire. See
   [`07-user-memory.md`](07-user-memory.md).

## This is also a Python learning project

A primary goal of building Tamara is **learning Python**. That is not incidental — it shapes
the plan: the backend is built in **small, individually reviewable increments**, each one
sized to be read, run, tested, and discussed before the next, and each tagged with the Python
concept it teaches. Architecture choices (FastAPI + Pydantic, an explicit
router→service→provider layering, typed everything) are made partly because they're a good,
modern way to learn Python. When implementing, **favor the small-step rhythm in
[`06-build-plan.md`](06-build-plan.md) over shipping big slices** — the constraint *is* the
curriculum.

## Contents

1. [`01-architecture-and-data-model.md`](01-architecture-and-data-model.md) — repo layout,
   runtime shape, full Postgres DDL + RLS (including the intake/draft tables).
2. [`02-api-contracts.md`](02-api-contracts.md) — every REST endpoint, request/response
   shapes, status codes, auth.
3. [`03-narrative-intake.md`](03-narrative-intake.md) — **the guided kernel→narrative
   questionnaire**: flow, state machine, agent operations, schemas, edge cases.
4. [`04-agent.md`](04-agent.md) — the Claude integration: context assembly, structured
   output, drafting/Q&A, provenance rules, prompts.
5. [`05-frontend.md`](05-frontend.md) — React/TS routes, components, state, the intake UI.
6. [`06-build-plan.md`](06-build-plan.md) — the incremental phases (intake + memory sequenced
   in), each step tagged with the Python concept it teaches.
7. [`07-user-memory.md`](07-user-memory.md) — **the per-user agentic memory system**: layers,
   types, write (propose-then-confirm), recall, and the MVP-vs-post-MVP split.

## Non-negotiable MVP guardrails (carried from the notes)

- **Equities only.** Crypto is post-MVP.
- **User-initiated only.** No schedulers, workers, queues, background hydration, or
  auto-feeds. Every external call (data fetch, LLM call, tweet resolve) happens because the
  user clicked or asked. The intake questionnaire is user-initiated and synchronous — it is
  *not* a background agent.
- **Build on redisplayable data.** SEC EDGAR (public domain) is the foundation; clear a
  display license before building UI on any paid provider's data.
- **Twitter is manual and last.** A pasted single tweet becomes a source; no firehose.
- **Backend in small, reviewable Python steps.** The build plan keeps each increment
  digestible (this is also a Python learning exercise).

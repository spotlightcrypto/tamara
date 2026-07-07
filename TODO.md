# Tamara — Completion Backlog

A living list of features and integrations that are **started, stubbed, or
deliberately deferred** — the things that need finishing before Tamara is
"complete." Grouped by area. Update as items land; move done items to the bottom
or delete them.

Status legend: 🟥 not started · 🟨 prototype/partial · 🟩 done (kept briefly for context)

---

## Paid / external API integrations

These are the ones that cost money or need an account + key, so they're gated on a
spend decision. Each has a working free/prototype path today.

- 🟨 **Polygon.io — bulk price ingest.** Prototype runs on Yahoo's keyless
  per-ticker chart endpoint (`providers/prices.py::daily_history`), which does not
  scale past our handful of tickers. Production path (`grouped_daily`) pulls the
  whole US market in one call but needs `POLYGON_API_KEY`.
  - [ ] Add the key to `backend/.env`.
  - [ ] Switch ingest to `grouped_daily`; wire a **daily cron** (post-close) and a
        **~15-min intraday cron** for delayed quotes.
  - [ ] Normalize class-share tickers dot→hyphen on ingest so keys align with
        `exchanges.yahoo_symbol` (see NOTE in `providers/prices.py`).
  - [ ] Run the history backfill against real Polygon data and confirm parity.
- 🟥 **Intraday windows (1H, live 1D).** Need a delayed snapshot feed (paid). Today
  we only compute daily windows (1D/1W/1M/3M/6M/1Y); `PricePerformance` already
  leaves `1H` as a seam.
- 🟥 **International price coverage — Tier 3.** Tier 1 (US) and Tier 2 (major
  developed, via Yahoo suffixes) are priced for free. Tier 3 is **narrative-only**
  (no price) by design until we add a paid all-world feed (EODHD / FMP candidates).
  The UI already shows "price coming soon" for these.
- 🟥 **Company hydration.** `sector`, `profile`, `fundamentals`, `last_hydrated_at`
  are placeholders on every company. Needs a data source (free or paid) + a
  hydrate step to fill them.
- 🟥 **X / Twitter login.** Researched (see below). Mechanically small via Supabase
  Auth (OAuth 2.0 provider + identity linking), but **gated on confirming that
  "Sign in with X" OAuth is free** under X's 2026 pay-per-use API regime — verify
  in the X Developer Portal before building.
  - [ ] Confirm login cost in the X dev portal.
  - [ ] Enable the X OAuth 2.0 provider in Supabase; add a "Sign in with X" button.
  - [ ] Enable **manual identity linking** + a "Link X" button on the profile page
        (X returns no email, so email auto-linking won't fire).

## Search (just shipped — follow-ups)

- 🟨 **Pre-seed intake with the exact resolved company.** The "write the first
  narrative" path currently pre-fills the kernel *text* with the ticker and lets
  the intake agent re-derive the company. Tighter UX: attach the resolved
  `(ticker, mic)` company to the draft directly.
- 🟥 **Relevance ranking + `pg_trgm`.** Local search is unranked `ilike` substring.
  For scale, add a trigram index on `companies(ticker, name)` and
  `narratives(title, thesis)` and order by similarity.
- 🟥 **ETFs / indices in the resolver.** External resolve filters to `EQUITY` only.

## Product features (spec'd / brainstormed, not built)

- 🟥 **Per-user agentic memory** (`spec/07-user-memory.md`). Deliberately deferred
  until we have a real dataset — revisit once there's usage to learn from.
- 🟥 **Dynamic / living narratives.** The 10 brainstormed ideas for making
  published narratives update over time — none built yet.
- 🟥 **Anti-slop friction.** Mechanisms that add signal-producing friction so
  ease-of-use doesn't converge on generic output. Design + build.
- 🟥 **Serious design / branding pass.** The acid-brutalist theme is a placeholder.

## Infra / quality

- 🟥 **Frontend code-splitting.** Bundle is >500 kB (one chunk). Dynamic-import the
  heavy routes (intake modal, editor) to cut initial load.
- 🟥 **Production CORS + hosting.** `main.py` allows only localhost origins in dev;
  set the real frontend origin for prod.
- 🟨 **`daily_bars` international keying.** Bars are keyed by the Yahoo/price symbol
  (unique across exchanges). Fine today; revisit if the Polygon US path (dot
  tickers) and Yahoo intl path (hyphen) ever need to coexist in one table.

---

## Recently completed

- 🟩 **International company identity (ticker, MIC).** Migration applied; attach
  resolves MIC via `app/exchanges.py`; tier-gated prices; `slug` = `ticker:mic`.
- 🟩 **Search v1.** Local combined search (`/search`) + external symbol resolver
  (`/companies/resolve`) + home search bar + "write the first narrative" landing
  for companies not yet in Tamara.

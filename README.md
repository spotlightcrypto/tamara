# Tamara

Tamara is an AI-assisted investment research workspace for developing and tracking
equity investment theses. Each thesis is a **narrative** that brings together an
argument, the companies it concerns, supporting sources, follow-up notes, and
stock-price performance.

Start with a rough idea, pasted text, an article, or a tweet. Tamara reads the
material, asks questions to sharpen your view, and proposes a narrative you can
edit before saving. The goal is to make your reasoning explicit: the bull and
bear cases, catalysts, risks, and questions that still need answering.

## Current status

Tamara is an early working prototype with a React frontend, a FastAPI backend,
and persistent storage and authentication. The main creation and research flows
are implemented; production deployment and several data integrations remain
unfinished. Current scope is equities; crypto support is deferred.

### Implemented

- **Guided narrative creation:** AI-generated questions adapt to your input and
  answers, then produce a title, thesis, positioning label, and research document.
- **Review and revision:** edit the proposal and its Markdown document, adjust
  associated companies, or ask the AI to regenerate it with specific instructions.
- **Company-linked research:** attach up to eight companies, review suggested
  related companies, and browse narratives by company. Listings use ticker and
  exchange MIC identifiers to distinguish international securities.
- **Search:** search narrative titles and theses alongside company names and
  tickers. An external equity resolver finds listings not yet in Tamara and offers
  a path to write their first narrative.
- **Notes and sources:** retain links to source material and add timestamped
  follow-up notes to an existing narrative. Article and tweet ingestion includes
  a paste-text fallback when a link cannot be read.
- **Price performance:** display cached daily closing prices and returns over
  1D, 1W, 1M, 3M, 6M, and 1Y, plus performance since a narrative was created.
  The prototype supports US and selected international listings through Yahoo
  price history; uncovered exchanges remain available for research without prices.
- **Visibility and lifecycle:** make narratives public or private, retire them,
  and reactivate them. Signed-in readers can view public narratives; logged-out
  visitors see a short teaser.
- **Accounts:** email magic-link login, unique usernames, author attribution,
  and a profile listing your narratives.

### Planned or incomplete

- Production price ingestion and scheduled refreshes, intraday prices, and
  broader international price coverage. A Polygon bulk-ingestion path exists but
  still needs configuration and validation.
- Company profiles, sectors, fundamentals, and alternative financial signals.
- Persistent per-user AI memory and narratives that update automatically over time.
- X login, improved search ranking, and ETF/index resolution.
- Production hosting and CORS configuration, frontend code splitting, and a
  broader design pass.

Price displays depend on previously ingested data; they are not live quotes.
AI drafting and research ingestion are initiated by the user. See [TODO.md](TODO.md)
for the detailed implementation backlog. The [specifications](spec/README.md)
also describe future functionality and should not be read as a list of shipped
features.

## Stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, and a Tiptap-based editor.
- **Backend:** Python, FastAPI, and Pydantic.
- **Database and authentication:** Supabase Postgres and Auth, with Row-Level
  Security and SQL migrations.
- **AI:** an OpenRouter gateway with configurable models for question generation
  and narrative synthesis, plus schema-validated structured responses.
- **Source ingestion:** Jina Reader and an HTML-fetch fallback for articles;
  FxTwitter for individual tweet links.
- **Market data:** Yahoo price history for the prototype and a Polygon
  bulk-ingestion integration awaiting production setup.

## Repository layout

```text
frontend/            React application
  src/               Pages, intake flow, editor, search, and API client
backend/             FastAPI application
  app/               Auth, models, routers, services, and providers
  migrations/        Database schema and Row-Level Security policies
  tests/             Backend pytest suite
spec/                Architecture, API contracts, and product specifications
TODO.md              Current backlog and integration status
```

## Local development

You need Python, Node.js 22 (see `frontend/.nvmrc`), a Supabase project, and an
OpenRouter API key for AI drafting. Apply the SQL files in `backend/migrations/`
in filename order to your Supabase database. Configure email magic-link sign-in
and allow your local frontend URL as an authentication redirect URL.

### Backend

From the repository root:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `OPENROUTER_API_KEY` in `backend/.env`.
Model settings are defined in [backend/app/config.py](backend/app/config.py);
override `LLM_MODEL` and `LLM_MODEL_FAST` to choose synthesis and question-generation
models.

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

Interactive API documentation is available at <http://127.0.0.1:8000/docs>.

### Frontend

In a separate terminal, from the repository root:

```bash
cd frontend
npm ci
cp .env.example .env
```

Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `frontend/.env` to the same
Supabase project's public connection values. `VITE_API_URL` defaults to
`http://localhost:8000` in the example configuration.

```bash
npm run dev
```

Open the local URL printed by Vite and sign in using an email magic link.

### Price data

After creating narratives with associated companies, the authenticated
`POST /prices/ingest/watchlist` endpoint can populate their supported daily price
histories through the prototype Yahoo provider. Price views read this cache.
The separate `POST /prices/ingest` bulk endpoint requires `POLYGON_API_KEY`.

## Checks

Run the backend tests from `backend/`:

```bash
.venv/bin/python -m pytest
```

Run frontend lint and the production build from `frontend/`:

```bash
npm run lint
npm run build
```

-- Companies: a shared/global cache of assets (equities for now), NOT per-user.
-- The same company row (e.g. NVDA) is referenced by many users' narratives.
--
-- Bare-bones for now: identity + placeholders for profile/fundamentals that a
-- later "hydrate" step (Phase D) will fill. No search/index yet.

create table companies (
    id               uuid        primary key default gen_random_uuid(),
    ticker           text        unique not null,        -- normalized upper-case, e.g. NVDA
    name             text        not null,
    exchange         text,
    sector           text,
    profile          jsonb,                               -- description + provider profile (hydrated later)
    fundamentals     jsonb,                               -- latest financials snapshot (hydrated later)
    last_hydrated_at timestamptz,                         -- null = never fetched
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

alter table companies enable row level security;

-- Shared cache: any signed-in user may READ companies, and (bare-bones) CREATE
-- them when attaching a ticker. We can tighten writes to a service-role client
-- once hydration arrives. `to authenticated` targets logged-in users (not anon).
create policy companies_read on companies
    for select to authenticated using (true);
create policy companies_insert on companies
    for insert to authenticated with check (true);

create trigger companies_set_updated_at
    before update on companies
    for each row execute function set_updated_at();

-- Many-to-many: which companies a narrative is about.
create table narrative_companies (
    narrative_id uuid        not null references narratives (id) on delete cascade,
    company_id   uuid        not null references companies (id)  on delete cascade,
    created_at   timestamptz not null default now(),
    primary key (narrative_id, company_id)
);

create index narrative_companies_company_idx on narrative_companies (company_id);

alter table narrative_companies enable row level security;

-- Gate the join through the parent narrative (RLS-via-parent, like items).
create policy narrative_companies_via_parent on narrative_companies
    for all
    using (
        exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
    )
    with check (
        exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
    );

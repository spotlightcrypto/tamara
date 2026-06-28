-- Narratives: a user's top-level thesis workspace — the first table in Tamara.
--
-- Applied to the "tamara ai" Supabase project via the Supabase MCP. This file is
-- the committed source of truth so the schema is reproducible.

create table narratives (
    id          uuid        primary key default gen_random_uuid(),
    user_id     uuid        not null references auth.users (id) on delete cascade,
    title       text        not null,
    thesis      text        not null default '',
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- Index for the most common query: "this user's narratives, most recently updated first".
create index narratives_user_updated_idx on narratives (user_id, updated_at desc);

-- Row-Level Security: Postgres itself filters every query so a user can only ever
-- see and modify their OWN narratives. This is the security backstop beneath the API.
alter table narratives enable row level security;

create policy narratives_owner on narratives
    for all
    using (user_id = auth.uid())        -- which existing rows this user may read/update/delete
    with check (user_id = auth.uid());  -- what values a user may insert/update into a row

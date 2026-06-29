-- Notes: a user's free-text annotations on a narrative.
-- Unlike narrative_items, notes carry their own user_id (owner-based RLS).
-- A `company_id` column (tying a note to a company) is deferred to Phase D,
-- once the companies table exists.

create table notes (
    id           uuid        primary key default gen_random_uuid(),
    user_id      uuid        not null references auth.users (id) on delete cascade,
    narrative_id uuid        not null references narratives (id) on delete cascade,
    body         text        not null,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create index notes_narrative_idx on notes (narrative_id);

-- Owner-based RLS: a user sees and edits only their own notes.
alter table notes enable row level security;

create policy notes_owner on notes
    for all
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

-- Maintain updated_at automatically (shared trigger function from an earlier migration).
create trigger notes_set_updated_at
    before update on notes
    for each row execute function set_updated_at();

-- Narrative drafts: a guided-intake session. Holds the kernel, the running Q&A
-- transcript, and the synthesized proposal. Promoted to a real narrative on
-- finalize. Per-user (owner RLS); short-lived.

create table narrative_drafts (
    id             uuid        primary key default gen_random_uuid(),
    user_id        uuid        not null references auth.users (id) on delete cascade,
    status         text        not null default 'collecting'
                   check (status in ('collecting', 'proposed', 'finalized', 'abandoned')),
    kernel_kind    text        not null check (kernel_kind in ('text', 'url', 'tweet', 'document')),
    kernel_raw     text,                                  -- pasted text / extracted document text
    kernel_url     text,
    kernel_title   text,                                  -- fetched (url/tweet)
    kernel_excerpt text,                                  -- fetched snippet
    round          int         not null default 0,        -- question rounds asked so far
    transcript     jsonb       not null default '[]'::jsonb,  -- ordered turns: questions + answers
    proposal       jsonb,                                 -- synthesized draft narrative
    narrative_id   uuid        references narratives (id) on delete set null,  -- set on finalize
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now()
);

create index narrative_drafts_user_status_idx
    on narrative_drafts (user_id, status, updated_at desc);

alter table narrative_drafts enable row level security;

create policy narrative_drafts_owner on narrative_drafts
    for all
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

create trigger narrative_drafts_set_updated_at
    before update on narrative_drafts
    for each row execute function set_updated_at();

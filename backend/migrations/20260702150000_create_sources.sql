-- Sources: external links a narrative is grounded in. When the intake kernel is
-- a link (or contains links), we capture each as a source so the finished
-- narrative shows where it came from — presented as a nicely-named external link.
--
-- Deferred from the original C3/C4 "sources" work; this is the minimal slice:
-- identity + a short display title. Item-level citations can come later.

create table sources (
    id           uuid        primary key default gen_random_uuid(),
    narrative_id uuid        not null references narratives (id) on delete cascade,
    url          text        not null,
    title        text        not null default '',  -- short "few words" display name
    created_at   timestamptz not null default now()
);

-- One source per (narrative, url): re-finalizing an intake shouldn't duplicate it.
create unique index sources_narrative_url_key on sources (narrative_id, url);

alter table sources enable row level security;

-- RLS-via-parent: you can touch a source only if you own its narrative.
create policy sources_via_parent on sources
    for all
    using (
        exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
    )
    with check (
        exists (select 1 from narratives n where n.id = narrative_id and n.user_id = auth.uid())
    );

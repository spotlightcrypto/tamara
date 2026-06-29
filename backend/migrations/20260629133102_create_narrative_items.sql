-- Narrative items: the bull / bear / catalyst / risk points of a narrative.
-- One table, discriminated by `kind`. Items have no user_id — ownership flows
-- through the parent narrative (see the RLS policy below).

create table narrative_items (
    id           uuid        primary key default gen_random_uuid(),
    narrative_id uuid        not null references narratives (id) on delete cascade,
    kind         text        not null check (kind in ('bull', 'bear', 'catalyst', 'risk')),
    body         text        not null,
    event_date   date,                                  -- only meaningful for catalysts
    position     int         not null default 0,        -- ordering within (narrative, kind)
    created_at   timestamptz not null default now()
);

-- The common read: a narrative's items, grouped by section and ordered.
create index narrative_items_narrative_kind_position_idx
    on narrative_items (narrative_id, kind, position);

-- RLS-via-parent: you may touch an item only if you own the narrative it belongs
-- to. Unlike narratives (which have user_id), ownership here is checked through
-- the parent row.
alter table narrative_items enable row level security;

create policy narrative_items_via_parent on narrative_items
    for all
    using (
        exists (
            select 1 from narratives n
            where n.id = narrative_id and n.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1 from narratives n
            where n.id = narrative_id and n.user_id = auth.uid()
        )
    );

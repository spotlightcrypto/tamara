-- Narratives become a publishing surface: public by default, world-readable (to
-- any signed-in user) and searchable. Owners can flip one private. Public scope
-- is the WHOLE narrative — body, companies, sources, and notes — so we relax
-- SELECT on the child tables to "owner OR parent is public". Writes stay
-- owner-only everywhere.

alter table narratives add column is_public boolean not null default true;
create index narratives_public_idx on narratives (is_public) where is_public;

-- narratives: split the single owner-ALL policy into a public-or-owner read and
-- owner-only writes.
drop policy narratives_owner on narratives;
create policy narratives_select on narratives for select
    using (user_id = auth.uid() or is_public);
create policy narratives_insert on narratives for insert
    with check (user_id = auth.uid());
create policy narratives_update on narratives for update
    using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy narratives_delete on narratives for delete
    using (user_id = auth.uid());

-- narrative_companies: readable when the parent is owned OR public; writes owner-only.
drop policy narrative_companies_via_parent on narrative_companies;
create policy narrative_companies_select on narrative_companies for select
    using (exists (select 1 from narratives n
                   where n.id = narrative_companies.narrative_id
                     and (n.user_id = auth.uid() or n.is_public)));
create policy narrative_companies_write on narrative_companies for all
    using (exists (select 1 from narratives n
                   where n.id = narrative_companies.narrative_id
                     and n.user_id = auth.uid()))
    with check (exists (select 1 from narratives n
                        where n.id = narrative_companies.narrative_id
                          and n.user_id = auth.uid()));

-- sources: same shape as narrative_companies.
drop policy sources_via_parent on sources;
create policy sources_select on sources for select
    using (exists (select 1 from narratives n
                   where n.id = sources.narrative_id
                     and (n.user_id = auth.uid() or n.is_public)));
create policy sources_write on sources for all
    using (exists (select 1 from narratives n
                   where n.id = sources.narrative_id
                     and n.user_id = auth.uid()))
    with check (exists (select 1 from narratives n
                        where n.id = sources.narrative_id
                          and n.user_id = auth.uid()));

-- notes: authored by the owner (write stays user_id-scoped), but readable by
-- anyone who can see the public parent narrative.
drop policy notes_owner on notes;
create policy notes_select on notes for select
    using (user_id = auth.uid()
           or exists (select 1 from narratives n
                      where n.id = notes.narrative_id and n.is_public));
create policy notes_insert on notes for insert with check (user_id = auth.uid());
create policy notes_update on notes for update
    using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy notes_delete on notes for delete using (user_id = auth.uid());

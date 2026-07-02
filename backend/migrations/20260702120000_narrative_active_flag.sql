-- Narratives get an active/inactive flag. Every narrative starts ACTIVE; the
-- owner can later mark one inactive (e.g. thesis played out or abandoned) without
-- deleting it. Inactive narratives are still readable — just visually demoted.
--
-- Backfill: `not null default true` makes every existing row active.

alter table narratives add column is_active boolean not null default true;

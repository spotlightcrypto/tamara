-- Narratives move from structured bull/bear/catalyst/risk items to a single
-- editable markdown document (`body_md`), plus a `positioning` label — an
-- auto-generated stance (megabull / permabull / normiebull / megabear /
-- ultrabear) the user can edit to anything.
--
-- `body_md` is backfilled from any existing narrative_items so narratives created
-- before this change still render on the detail page.

alter table narratives add column positioning text;
alter table narratives add column body_md    text not null default '';

-- Backfill: compose a markdown doc from existing structured items, grouped by
-- kind in bull -> bear -> catalyst -> risk order.
with parts as (
    select narrative_id,
           kind,
           '## ' || initcap(kind) as heading,
           string_agg('- ' || body, E'\n' order by position) as bullets
    from narrative_items
    group by narrative_id, kind
),
docs as (
    select narrative_id,
           string_agg(
               heading || E'\n' || bullets,
               E'\n\n'
               order by case kind
                   when 'bull' then 1 when 'bear' then 2
                   when 'catalyst' then 3 when 'risk' then 4 else 5 end
           ) as md
    from parts
    group by narrative_id
)
update narratives n
set body_md = docs.md
from docs
where docs.narrative_id = n.id
  and (n.body_md is null or n.body_md = '');

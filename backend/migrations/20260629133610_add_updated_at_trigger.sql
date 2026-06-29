-- Add updated_at to narrative_items, and stop maintaining updated_at by hand.
-- A shared BEFORE UPDATE trigger now stamps updated_at on every row update, for
-- every table it's attached to — so we can never forget it on a new table.

alter table narrative_items
    add column updated_at timestamptz not null default now();

-- Generic trigger function: set updated_at to "now" on any UPDATE.
-- `set search_path = ''` keeps it from depending on the caller's search path
-- (a security-linter best practice); now() lives in pg_catalog, always available.
create or replace function set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger narratives_set_updated_at
    before update on narratives
    for each row execute function set_updated_at();

create trigger narrative_items_set_updated_at
    before update on narrative_items
    for each row execute function set_updated_at();

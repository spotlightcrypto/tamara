-- Profiles: a user's PUBLIC identity — a unique username, decoupled from the
-- private email in auth.users. Everything else in the app references the
-- immutable user_id (this table's `id`), never the username string, so a user
-- can rename freely without breaking ownership, joins, or (future) follows.

create table profiles (
    id         uuid        primary key references auth.users (id) on delete cascade,
    username   text        not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Case-insensitive uniqueness. We also store usernames lowercase, so this mainly
-- guards against any stray non-lowercase insert.
create unique index profiles_username_lower_key on profiles (lower(username));

alter table profiles enable row level security;

-- Usernames are PUBLIC to any signed-in user (needed to show @author on cards and
-- resolve /u/:username later). A user may write only their OWN profile row.
create policy profiles_read       on profiles for select to authenticated using (true);
create policy profiles_insert_own on profiles for insert to authenticated with check (id = auth.uid());
create policy profiles_update_own on profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

create trigger profiles_set_updated_at
    before update on profiles
    for each row execute function set_updated_at();

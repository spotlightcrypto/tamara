-- Let a user delete their OWN profile (frees the username; the account and its
-- narratives persist, and the first-login gate makes them pick a new one).
create policy profiles_delete_own on profiles
    for delete to authenticated using (id = auth.uid());

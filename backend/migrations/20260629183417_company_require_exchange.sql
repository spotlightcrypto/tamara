-- A ticker is meaningless without its exchange, so exchange is now REQUIRED.
-- Identity stays (ticker, exchange), but exchange can no longer be null.

-- Clear any pre-existing rows with an unknown (null) exchange — these were
-- dev/test artifacts created before this rule. No-op on a fresh database.
delete from companies where exchange is null;

-- Replace the coalesce() unique index (which existed to tolerate null exchange)
-- with a plain composite unique, and make the column NOT NULL.
drop index companies_ticker_exchange_key;
alter table companies alter column exchange set not null;
create unique index companies_ticker_exchange_key on companies (ticker, exchange);

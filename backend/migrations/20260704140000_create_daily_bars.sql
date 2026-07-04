-- Daily price bars: our LOCAL cache of the market. Rather than call a price API
-- per ticker (which never scales to thousands of tickers), we ingest the whole
-- market in bulk once per trading day (Polygon "Grouped Daily" = all US tickers
-- in one call) and store it here. Every price-performance lookup is then a fast
-- read against our own Postgres — decoupled from ticker count and API cost.
--
-- Covers the daily timeframes (1D/1W/1M/3M/6M/1Y). Intraday (1H, live 1D) needs
-- a delayed snapshot feed (paid) and is left as a later seam.

create table daily_bars (
    ticker text    not null,               -- bare US ticker, e.g. AAPL (Polygon style)
    date   date    not null,               -- trading date
    close  numeric not null,               -- adjusted close
    volume bigint,
    primary key (ticker, date)             -- the PK btree also serves lookups by
);                                         -- (ticker, date desc) — no extra index needed

-- Global reference data (not per-user), like the companies cache: any signed-in
-- user may read; the ingest path (authenticated for now) may write. We can move
-- writes to a service-role/cron client later without changing readers.
alter table daily_bars enable row level security;

create policy daily_bars_read on daily_bars
    for select to authenticated using (true);
create policy daily_bars_write on daily_bars
    for insert to authenticated with check (true);
create policy daily_bars_update on daily_bars
    for update to authenticated using (true) with check (true);

-- Move company identity from (ticker, exchange-name) to (ticker, MIC) so we can
-- represent international listings unambiguously. `exchange` stays as the friendly
-- display name; `mic` is the ISO 10383 canonical code. Adds currency/country/tier
-- for the tiered price-coverage model.

alter table companies add column mic      text;
alter table companies add column currency text;
alter table companies add column country  text;
alter table companies add column tier     int;

-- Backfill existing rows (all US so far) from their friendly exchange name.
update companies
set mic = case upper(exchange)
              when 'NASDAQ' then 'XNAS'
              when 'NYSE'   then 'XNYS'
              else upper(exchange)
          end,
    currency = 'USD',
    country  = 'US',
    tier     = 1;

alter table companies alter column mic set not null;

-- Identity is now (ticker, mic).
drop index companies_ticker_exchange_key;
create unique index companies_ticker_mic_key on companies (ticker, mic);

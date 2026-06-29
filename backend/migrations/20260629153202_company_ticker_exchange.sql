-- A bare ticker is ambiguous: the same symbol can trade on different exchanges
-- (e.g. CRWV:NASDAQ). The company's identity is the (ticker, exchange) pair.
--
-- We replace the unique(ticker) constraint with a unique index over
-- (ticker, coalesce(exchange, '')). The coalesce means a company whose exchange
-- isn't known yet (exchange = null) still dedupes by ticker to a single row,
-- while a known exchange makes a distinct identity.

alter table companies drop constraint companies_ticker_key;

create unique index companies_ticker_exchange_key
    on companies (ticker, coalesce(exchange, ''));

"""Tests for bare-bones companies.

Companies are GLOBAL/shared (no user_id) and we don't expose a delete for them,
so company rows persist across runs — that's fine, get-or-create is idempotent.
A company's identity is the exchange-qualified (ticker, exchange); an exchange is
required. Tests assert on behavior, never on absolute counts. narrative_companies
links cascade-delete with their parent narrative.
"""

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def test_attach_qualified_ticker_normalizes(client, make_narrative):
    n = make_narrative()
    r = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "crwv:nasdaq"})
    assert r.status_code == 201
    company = r.json()
    assert company["ticker"] == "CRWV"          # upper-cased
    assert company["exchange"] == "NASDAQ"      # friendly display name
    assert company["mic"] == "XNAS"             # canonical identity (resolved)
    assert company["currency"] == "USD"
    assert company["country"] == "US"
    assert company["tier"] == 1
    assert company["symbol"] == "CRWV:NASDAQ"   # friendly derived field
    assert company["slug"] == "crwv:xnas"       # canonical URL slug (ticker:mic)
    assert company["name"] == "CRWV"            # defaults to ticker (no hydration)
    assert company["last_hydrated_at"] is None


def test_attach_international_resolves_tier_and_currency(client, make_narrative):
    n = make_narrative()
    # A London listing: friendly "LSE" resolves to MIC XLON, tier 2, GBP.
    company = client.post(
        f"/narratives/{n['id']}/companies", json={"ticker": "BARC:LSE", "name": "Barclays"}
    ).json()
    assert company["mic"] == "XLON"
    assert company["exchange"] == "London Stock Exchange"
    assert company["currency"] == "GBP"
    assert company["country"] == "GB"
    assert company["tier"] == 2
    assert company["slug"] == "barc:xlon"


def test_attach_unknown_exchange_is_tier3_passthrough(client, make_narrative):
    n = make_narrative()
    # An exchange we don't know: still creatable (narrative-only), tier 3, no price.
    company = client.post(
        f"/narratives/{n['id']}/companies", json={"ticker": "ZZZCO", "exchange": "ZZQQ"}
    ).json()
    assert company["mic"] == "ZZQQ"      # passthrough key
    assert company["tier"] == 3
    assert company["currency"] is None
    assert company["slug"] == "zzzco:zzqq"


def test_attach_with_separate_exchange_field(client, make_narrative):
    n = make_narrative()
    company = client.post(
        f"/narratives/{n['id']}/companies",
        json={"ticker": "vst", "exchange": "nyse", "name": "Vistra"},
    ).json()
    assert company["ticker"] == "VST"
    assert company["exchange"] == "NYSE"
    assert company["name"] == "Vistra"


def test_attach_without_exchange_is_rejected(client, make_narrative):
    n = make_narrative()
    # Bare ticker, no exchange anywhere -> 422
    assert client.post(f"/narratives/{n['id']}/companies", json={"ticker": "NVDA"}).status_code == 422


def test_same_ticker_different_exchange_are_distinct(client, make_narrative):
    n = make_narrative()
    a = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "DUAL:NASDAQ"}).json()
    b = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "DUAL:NYSE"}).json()
    assert a["id"] != b["id"]  # exchange is part of the identity


def test_same_symbol_is_one_shared_company(client, make_narrative):
    a = make_narrative()
    b = make_narrative()
    ca = client.post(f"/narratives/{a['id']}/companies", json={"ticker": "CEG:NASDAQ"}).json()
    cb = client.post(f"/narratives/{b['id']}/companies", json={"ticker": "CEG:NASDAQ"}).json()
    assert ca["id"] == cb["id"]  # same global company row


def test_attach_is_idempotent(client, make_narrative):
    n = make_narrative()
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "AAPL:NASDAQ"})
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "AAPL:NASDAQ"})
    companies = client.get(f"/narratives/{n['id']}/companies").json()
    assert [c["ticker"] for c in companies].count("AAPL") == 1


def test_list_companies(client, make_narrative):
    n = make_narrative()
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "MSFT:NASDAQ"})
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "GOOG:NASDAQ"})
    tickers = {c["ticker"] for c in client.get(f"/narratives/{n['id']}/companies").json()}
    assert {"MSFT", "GOOG"} <= tickers


def test_detach_company(client, make_narrative):
    n = make_narrative()
    company = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "AMZN:NASDAQ"}).json()
    assert client.delete(f"/narratives/{n['id']}/companies/{company['id']}").status_code == 204
    tickers = [c["ticker"] for c in client.get(f"/narratives/{n['id']}/companies").json()]
    assert "AMZN" not in tickers


def test_attach_on_missing_narrative_returns_404(client):
    assert client.post(
        f"/narratives/{MISSING_ID}/companies", json={"ticker": "NVDA:NASDAQ"}
    ).status_code == 404


def test_attach_requires_ticker(client, make_narrative):
    n = make_narrative()
    assert client.post(f"/narratives/{n['id']}/companies", json={}).status_code == 422


def test_get_company_by_id(client, make_narrative):
    n = make_narrative()
    company = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "TSLA:NASDAQ"}).json()
    fetched = client.get(f"/companies/{company['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["symbol"] == "TSLA:NASDAQ"


def test_get_missing_company_returns_404(client):
    assert client.get(f"/companies/{MISSING_ID}").status_code == 404


def test_get_company_by_symbol(client, make_narrative):
    n = make_narrative()
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "AMD:NASDAQ"})
    # The readable route resolves the exchange segment to a MIC, so both the new
    # slug (amd:xnas) and the older friendly form (amd:nasdaq) fetch the same row.
    for seg in ("xnas", "nasdaq"):
        fetched = client.get(f"/companies/by-symbol/amd/{seg}")
        assert fetched.status_code == 200
        assert fetched.json()["slug"] == "amd:xnas"
    assert client.get("/companies/by-symbol/NOPE/NASDAQ").status_code == 404


def test_detach_missing_link_returns_404(client, make_narrative):
    n = make_narrative()
    assert client.delete(
        f"/narratives/{n['id']}/companies/{MISSING_ID}"
    ).status_code == 404


def test_companies_require_auth(unauth_client):
    assert unauth_client.get(f"/narratives/{MISSING_ID}/companies").status_code == 401

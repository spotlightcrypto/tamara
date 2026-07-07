"""Tests for search: the reverse Yahoo->(ticker, MIC) resolver, combined local
search (narratives + companies), and the external symbol resolver (mocked)."""

from app import exchanges


# --- exchanges.from_yahoo (pure) ----------------------------------------------

def test_from_yahoo_us_by_exchange_code():
    # US listings have no suffix; the Yahoo exchange code resolves the MIC.
    assert exchanges.from_yahoo("AAPL", "NMS")[:2] == ("AAPL", "XNAS")
    assert exchanges.from_yahoo("PLTR", "NYQ")[:2] == ("PLTR", "XNYS")


def test_from_yahoo_class_share_hyphen_becomes_dot():
    ticker, mic, _ = exchanges.from_yahoo("BRK-B", "NYQ")
    assert (ticker, mic) == ("BRK.B", "XNYS")


def test_from_yahoo_international_by_suffix():
    # The symbol suffix is authoritative for non-US listings.
    assert exchanges.from_yahoo("BARC.L", "LSE")[:2] == ("BARC", "XLON")
    assert exchanges.from_yahoo("7203.T", "JPX")[:2] == ("7203", "XTKS")


def test_from_yahoo_unknown_is_tier3_passthrough():
    ticker, mic, meta = exchanges.from_yahoo("FOO", "ZZQQ")
    assert ticker == "FOO"
    assert meta["tier"] == 3
    assert meta["yahoo"] is None  # no price source


# --- combined local search -----------------------------------------------------

def test_search_finds_narrative_by_title(client, make_narrative):
    make_narrative(title="Zqxsearch Uranium Supercycle", thesis="a thesis")
    hits = client.get("/search", params={"q": "zqxsearch"}).json()
    titles = [n["title"] for n in hits["narratives"]]
    assert any("Zqxsearch" in t for t in titles)


def test_search_finds_company_by_ticker(client, make_narrative):
    n = make_narrative()
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "ZQXSRCH:NASDAQ"})
    hits = client.get("/search", params={"q": "zqxsrch"}).json()
    assert "ZQXSRCH" in [c["ticker"] for c in hits["companies"]]


def test_search_requires_auth(unauth_client):
    assert unauth_client.get("/search", params={"q": "anything"}).status_code == 401


# --- external symbol resolver (provider mocked) --------------------------------

def test_resolve_external_maps_hits(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.companies.prices_provider.search_symbols",
        lambda q, limit=8: [
            {"symbol": "AAPL", "exchange": "NMS", "name": "Apple Inc."},
            {"symbol": "BARC.L", "exchange": "LSE", "name": "Barclays PLC"},
        ],
    )
    results = client.get("/companies/resolve", params={"q": "apple"}).json()
    by_ticker = {r["ticker"]: r for r in results}

    assert by_ticker["AAPL"]["mic"] == "XNAS"
    assert by_ticker["AAPL"]["slug"] == "aapl:xnas"
    assert by_ticker["AAPL"]["has_price"] is True

    assert by_ticker["BARC"]["mic"] == "XLON"
    assert by_ticker["BARC"]["currency"] == "GBP"
    assert by_ticker["BARC"]["tier"] == 2
    assert by_ticker["BARC"]["has_price"] is True


def test_resolve_external_tier3_has_no_price(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.companies.prices_provider.search_symbols",
        lambda q, limit=8: [{"symbol": "XYZ", "exchange": "ZZQQ", "name": "Obscure Co"}],
    )
    results = client.get("/companies/resolve", params={"q": "obscure"}).json()
    assert results[0]["tier"] == 3
    assert results[0]["has_price"] is False


def test_resolve_requires_auth(unauth_client):
    assert unauth_client.get("/companies/resolve", params={"q": "x"}).status_code == 401

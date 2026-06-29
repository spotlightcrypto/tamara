"""Tests for bare-bones companies.

Companies are GLOBAL/shared (no user_id) and we don't expose a delete for them,
so company rows persist across runs — that's fine, get-or-create is idempotent.
These tests use real tickers and assert on behavior, never on absolute counts.
The narrative_companies links cascade-delete with their parent narrative.
"""

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def test_attach_company_normalizes_ticker(client, make_narrative):
    n = make_narrative()
    r = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "nvda"})
    assert r.status_code == 201
    company = r.json()
    assert company["ticker"] == "NVDA"  # upper-cased
    assert company["name"] == "NVDA"    # defaults to ticker (no hydration yet)
    assert company["last_hydrated_at"] is None


def test_attach_with_name(client, make_narrative):
    n = make_narrative()
    company = client.post(
        f"/narratives/{n['id']}/companies", json={"ticker": "VST", "name": "Vistra"}
    ).json()
    assert company["ticker"] == "VST"
    assert company["name"] == "Vistra"


def test_same_ticker_is_one_shared_company(client, make_narrative):
    a = make_narrative()
    b = make_narrative()
    ca = client.post(f"/narratives/{a['id']}/companies", json={"ticker": "CEG"}).json()
    cb = client.post(f"/narratives/{b['id']}/companies", json={"ticker": "CEG"}).json()
    assert ca["id"] == cb["id"]  # same global company row


def test_attach_is_idempotent(client, make_narrative):
    n = make_narrative()
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "AAPL"})
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "AAPL"})
    companies = client.get(f"/narratives/{n['id']}/companies").json()
    assert [c["ticker"] for c in companies].count("AAPL") == 1


def test_list_companies(client, make_narrative):
    n = make_narrative()
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "MSFT"})
    client.post(f"/narratives/{n['id']}/companies", json={"ticker": "GOOG"})
    tickers = {c["ticker"] for c in client.get(f"/narratives/{n['id']}/companies").json()}
    assert {"MSFT", "GOOG"} <= tickers


def test_detach_company(client, make_narrative):
    n = make_narrative()
    company = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "AMZN"}).json()
    assert client.delete(f"/narratives/{n['id']}/companies/{company['id']}").status_code == 204
    tickers = [c["ticker"] for c in client.get(f"/narratives/{n['id']}/companies").json()]
    assert "AMZN" not in tickers


def test_attach_on_missing_narrative_returns_404(client):
    assert client.post(
        f"/narratives/{MISSING_ID}/companies", json={"ticker": "NVDA"}
    ).status_code == 404


def test_attach_requires_ticker(client, make_narrative):
    n = make_narrative()
    assert client.post(f"/narratives/{n['id']}/companies", json={}).status_code == 422


def test_get_company_by_id(client, make_narrative):
    n = make_narrative()
    company = client.post(f"/narratives/{n['id']}/companies", json={"ticker": "TSLA"}).json()
    fetched = client.get(f"/companies/{company['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["ticker"] == "TSLA"


def test_get_missing_company_returns_404(client):
    assert client.get(f"/companies/{MISSING_ID}").status_code == 404


def test_detach_missing_link_returns_404(client, make_narrative):
    n = make_narrative()
    assert client.delete(
        f"/narratives/{n['id']}/companies/{MISSING_ID}"
    ).status_code == 404


def test_companies_require_auth(unauth_client):
    assert unauth_client.get(f"/narratives/{MISSING_ID}/companies").status_code == 401

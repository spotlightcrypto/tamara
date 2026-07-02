"""Hermetic tests for the tiered URL ingestion — httpx is mocked, no network."""

import httpx

from app.models import IngestReason, KernelKind
from app.providers.ingest import ingest_url

LONG = "This is a substantial article body sentence. " * 12  # > 200 chars


def _resp(status: int = 200, *, json=None, text=None):
    """Build a fresh httpx.Response for a given URL (exactly one content kwarg)."""

    def make(url: str) -> httpx.Response:
        kwargs = {"request": httpx.Request("GET", url)}
        if json is not None:
            kwargs["json"] = json
        else:
            kwargs["text"] = text if text is not None else ""
        return httpx.Response(status, **kwargs)

    return make


def _patch_get(monkeypatch, routes):
    """Route httpx.get by URL substring; unrouted URLs raise ConnectError."""

    def fake_get(url, **kwargs):
        for substring, factory in routes:
            if substring in url:
                return factory(url)
        raise httpx.ConnectError("unrouted", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)


def test_invalid_url():
    result = ingest_url("not a url")
    assert not result.ok and result.reason == IngestReason.invalid_url


def test_tweet_via_fxtwitter(monkeypatch):
    _patch_get(monkeypatch, [
        ("api.fxtwitter.com",
         _resp(json={"tweet": {"text": "just setting up my twttr", "author": {"screen_name": "jack"}}})),
    ])
    result = ingest_url("https://twitter.com/jack/status/20")
    assert result.ok and result.source_kind == KernelKind.tweet
    assert result.title == "@jack"
    assert "twttr" in result.excerpt


def test_article_via_jina(monkeypatch):
    _patch_get(monkeypatch, [
        ("r.jina.ai", _resp(json={"data": {"title": "Memory Wall", "content": LONG}})),
    ])
    result = ingest_url("https://example.com/memory")
    assert result.ok and result.source_kind == KernelKind.url
    assert result.title == "Memory Wall"
    assert len(result.excerpt) >= 200


def test_article_falls_back_to_bs4_when_jina_thin(monkeypatch):
    html = f"<html><head><title>BS4 Title</title></head><body><p>{LONG}</p></body></html>"
    _patch_get(monkeypatch, [
        ("r.jina.ai", _resp(json={"data": {"title": None, "content": "tiny"}})),  # too thin
        ("example.com", _resp(text=html)),                                        # bs4 tier
    ])
    result = ingest_url("https://example.com/article")
    assert result.ok and result.title == "BS4 Title"
    assert len(result.excerpt) >= 200


def test_blocked_when_all_tiers_403(monkeypatch):
    _patch_get(monkeypatch, [
        ("r.jina.ai", _resp(403)),
        ("example.com", _resp(403)),
    ])
    result = ingest_url("https://example.com/paywalled")
    assert not result.ok and result.reason == IngestReason.blocked


def test_empty_when_no_substantive_content(monkeypatch):
    _patch_get(monkeypatch, [
        ("r.jina.ai", _resp(json={"data": {"title": "x", "content": ""}})),
        ("example.com", _resp(text="<html><body><nav>menu</nav></body></html>")),
    ])
    result = ingest_url("https://example.com/thin")
    assert not result.ok and result.reason == IngestReason.empty


def test_unreachable_when_connect_fails(monkeypatch):
    _patch_get(monkeypatch, [])  # every call raises ConnectError
    result = ingest_url("https://example.com/down")
    assert not result.ok and result.reason == IngestReason.unreachable

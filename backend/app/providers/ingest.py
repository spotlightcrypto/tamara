"""Tiered, fail-soft URL ingestion for the intake flow.

Goal: turn a pasted link into usable content (title + excerpt) — or a clean,
recoverable error — so a narrative always has something to launch from.

Tiers (free stack):
  - X/Twitter URLs  -> FxTwitter public JSON (api.fxtwitter.com), no auth.
  - Other URLs      -> Jina Reader (r.jina.ai, free) -> [paid fallback slot]
                       -> our basic bs4 fetch (last resort).
Then validate the content length; anything too thin is reported as `empty`.

`ingest_url` never raises — it always returns an `IngestResult`.
"""

from urllib.parse import urlparse

import httpx

from app.models import IngestReason, IngestResult, KernelKind
from app.providers.fetch import FetchError, fetch_url

_USER_AGENT = "Tamara/0.1 (+https://onspotlight.app; michael@onspotlight.app)"
_MIN_CONTENT = 200      # chars of substantive text required to be "usable"
_MAX_EXCERPT = 4000
_TWITTER_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}


def ingest_url(raw: str) -> IngestResult:
    """Ingest a URL into an IngestResult (never raises)."""
    url = raw.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return IngestResult(ok=False, source_kind=KernelKind.url, url=url, reason=IngestReason.invalid_url)

    if parsed.netloc.lower() in _TWITTER_HOSTS and "/status/" in parsed.path:
        return _ingest_tweet(url)
    return _ingest_article(url)


# --- X / Twitter -----------------------------------------------------------

def _ingest_tweet(url: str) -> IngestResult:
    parsed = urlparse(url)
    api = f"https://api.fxtwitter.com{parsed.path}"
    try:
        resp = httpx.get(api, headers={"User-Agent": _USER_AGENT}, timeout=15.0, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError:
        return IngestResult(ok=False, source_kind=KernelKind.tweet, url=url, reason=IngestReason.unreachable)

    tweet = data.get("tweet") or {}
    text = (tweet.get("text") or "").strip()
    author = (tweet.get("author") or {}).get("screen_name")
    if not text:
        return IngestResult(ok=False, source_kind=KernelKind.tweet, url=url, reason=IngestReason.empty)

    title = f"@{author}" if author else "Tweet"
    return IngestResult(ok=True, source_kind=KernelKind.tweet, url=url, title=title, excerpt=text[:_MAX_EXCERPT])


# --- Articles / pages ------------------------------------------------------

def _ingest_article(url: str) -> IngestResult:
    title: str | None = None
    content = ""
    blocked = False
    unreachable = False

    # Tier 1: Jina Reader (free) — clean markdown, renders JS.
    try:
        title, content = _jina_read(url)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 402, 403, 451):
            blocked = True
    except httpx.HTTPError:
        unreachable = True

    # Tier 2: [paid fallback slot — Firecrawl/Tavily] would go here, enabled by config.
    # TODO

    # Tier 3: our basic bs4 fetch, if Jina came back thin.
    if len(content.strip()) < _MIN_CONTENT:
        try:
            t2, c2 = fetch_url(url)
            if len(c2.strip()) > len(content.strip()):
                title, content = (t2 or title), c2
        except FetchError:
            pass

    content = content.strip()[:_MAX_EXCERPT]
    if len(content) >= _MIN_CONTENT:
        return IngestResult(ok=True, source_kind=KernelKind.url, url=url, title=title, excerpt=content)

    # Couldn't get usable content — pick the most informative reason.
    reason = (
        IngestReason.blocked if blocked
        else IngestReason.unreachable if unreachable
        else IngestReason.empty
    )
    return IngestResult(ok=False, source_kind=KernelKind.url, url=url, title=title, reason=reason)


def _jina_read(url: str) -> tuple[str | None, str]:
    """Ask Jina Reader for cleaned content as JSON: {data: {title, content}}."""
    resp = httpx.get(
        f"https://r.jina.ai/{url}",
        headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return data.get("title"), (data.get("content") or "")

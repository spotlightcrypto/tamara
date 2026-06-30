"""URL fetch tool for the intake flow.

Given a URL, fetch the page and extract a title + a text excerpt — enough for
the LLM to understand the kernel. Deterministic; fails gracefully so intake can
degrade to "use the raw text" rather than crashing.
"""

import httpx
from bs4 import BeautifulSoup

# SEC and most sites want a contact-info User-Agent; be a good citizen.
_USER_AGENT = "Tamara/0.1 (+https://onspotlight.app; michael@onspotlight.app)"
_MAX_EXCERPT = 2000  # chars


class FetchError(Exception):
    """Raised when a URL can't be fetched/parsed."""


def fetch_url(url: str) -> tuple[str | None, str]:
    """Return (title, excerpt) for a web page. Raises FetchError on failure."""
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=15.0,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FetchError(f"could not fetch {url}: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    return _title(soup), _excerpt(soup)


def _title(soup: BeautifulSoup) -> str | None:
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return str(og["content"]).strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None


def _excerpt(soup: BeautifulSoup) -> str:
    """Meta description (if any) followed by the page's substantive paragraphs,
    truncated. Crude but enough to ground the LLM."""
    parts: list[str] = []

    desc = soup.find("meta", attrs={"name": "description"})
    if desc and desc.get("content"):
        parts.append(str(desc["content"]).strip())

    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text) > 40:  # skip nav/boilerplate fragments
            parts.append(text)
        if sum(len(x) for x in parts) > _MAX_EXCERPT:
            break

    return "\n\n".join(parts)[:_MAX_EXCERPT].strip()

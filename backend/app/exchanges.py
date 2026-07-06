"""Exchange registry — the source of truth for the exchange side of our
`ticker:MIC` identity model.

We key equities on (ticker, MIC) where MIC is the ISO 10383 Market Identifier
Code (XNAS, XLON, XTKS, …) — unambiguous and international, unlike a friendly
name string. Each exchange also carries:
  - name:     friendly display name ("NASDAQ")
  - yahoo:    Yahoo Finance symbol suffix ("" for US, "L" for LSE, …), or None
              if we don't have a free price source for it yet
  - currency, country
  - tier:     1 = US (deepest/cheapest data), 2 = major developed markets we can
              still price for free via Yahoo, 3 = everything else (narrative-only
              for now — no price until we add a paid all-world feed)

Price coverage is gated on `yahoo` (None -> no free price). Tier is used for
ranking/rollout, not for blocking narrative creation: any equity is creatable.
"""

# MIC -> metadata. Extend freely; unknown exchanges fall through to tier 3.
EXCHANGES: dict[str, dict] = {
    # --- Tier 1: US ---
    "XNAS": {"name": "NASDAQ", "yahoo": "", "currency": "USD", "country": "US", "tier": 1},
    "XNYS": {"name": "NYSE", "yahoo": "", "currency": "USD", "country": "US", "tier": 1},
    "ARCX": {"name": "NYSE Arca", "yahoo": "", "currency": "USD", "country": "US", "tier": 1},
    "XASE": {"name": "NYSE American", "yahoo": "", "currency": "USD", "country": "US", "tier": 1},
    "BATS": {"name": "Cboe BZX", "yahoo": "", "currency": "USD", "country": "US", "tier": 1},
    # --- Tier 2: major developed markets (free via Yahoo suffixes) ---
    "XLON": {"name": "London Stock Exchange", "yahoo": "L", "currency": "GBP", "country": "GB", "tier": 2},
    "XTKS": {"name": "Tokyo Stock Exchange", "yahoo": "T", "currency": "JPY", "country": "JP", "tier": 2},
    "XHKG": {"name": "Hong Kong Stock Exchange", "yahoo": "HK", "currency": "HKD", "country": "HK", "tier": 2},
    "XETR": {"name": "XETRA", "yahoo": "DE", "currency": "EUR", "country": "DE", "tier": 2},
    "XPAR": {"name": "Euronext Paris", "yahoo": "PA", "currency": "EUR", "country": "FR", "tier": 2},
    "XAMS": {"name": "Euronext Amsterdam", "yahoo": "AS", "currency": "EUR", "country": "NL", "tier": 2},
    "XBRU": {"name": "Euronext Brussels", "yahoo": "BR", "currency": "EUR", "country": "BE", "tier": 2},
    "XLIS": {"name": "Euronext Lisbon", "yahoo": "LS", "currency": "EUR", "country": "PT", "tier": 2},
    "XMIL": {"name": "Borsa Italiana", "yahoo": "MI", "currency": "EUR", "country": "IT", "tier": 2},
    "XMAD": {"name": "Bolsa de Madrid", "yahoo": "MC", "currency": "EUR", "country": "ES", "tier": 2},
    "XTSE": {"name": "Toronto Stock Exchange", "yahoo": "TO", "currency": "CAD", "country": "CA", "tier": 2},
    "XASX": {"name": "Australian Securities Exchange", "yahoo": "AX", "currency": "AUD", "country": "AU", "tier": 2},
    "XSWX": {"name": "SIX Swiss Exchange", "yahoo": "SW", "currency": "CHF", "country": "CH", "tier": 2},
    "XSTO": {"name": "Nasdaq Stockholm", "yahoo": "ST", "currency": "SEK", "country": "SE", "tier": 2},
    "XCSE": {"name": "Nasdaq Copenhagen", "yahoo": "CO", "currency": "DKK", "country": "DK", "tier": 2},
    "XOSL": {"name": "Oslo Bors", "yahoo": "OL", "currency": "NOK", "country": "NO", "tier": 2},
    "XNSE": {"name": "NSE India", "yahoo": "NS", "currency": "INR", "country": "IN", "tier": 2},
    "XBOM": {"name": "BSE India", "yahoo": "BO", "currency": "INR", "country": "IN", "tier": 2},
    "XKRX": {"name": "Korea Exchange", "yahoo": "KS", "currency": "KRW", "country": "KR", "tier": 2},
    "XTAI": {"name": "Taiwan Stock Exchange", "yahoo": "TW", "currency": "TWD", "country": "TW", "tier": 2},
    "XSHG": {"name": "Shanghai Stock Exchange", "yahoo": "SS", "currency": "CNY", "country": "CN", "tier": 2},
    "XSHE": {"name": "Shenzhen Stock Exchange", "yahoo": "SZ", "currency": "CNY", "country": "CN", "tier": 2},
    "XSAO": {"name": "B3 (Brazil)", "yahoo": "SA", "currency": "BRL", "country": "BR", "tier": 2},
    "XJSE": {"name": "Johannesburg Stock Exchange", "yahoo": "JO", "currency": "ZAR", "country": "ZA", "tier": 2},
}

# Friendly names, common aliases, and Yahoo exchange codes -> MIC. Everything is
# matched upper-cased. This lets us resolve whatever the LLM, a user, or Yahoo's
# search hands us into a canonical MIC.
ALIASES: dict[str, str] = {
    "NASDAQ": "XNAS", "NMS": "XNAS", "NGM": "XNAS", "NCM": "XNAS", "NASDAQGS": "XNAS",
    "NYSE": "XNYS", "NYQ": "XNYS", "NYE": "XNYS",
    "NYSEARCA": "ARCX", "ARCA": "ARCX", "PCX": "ARCX",
    "AMEX": "XASE", "NYSE AMERICAN": "XASE", "ASE": "XASE", "NYSEAMERICAN": "XASE",
    "CBOE": "BATS", "BZX": "BATS",
    "LSE": "XLON", "LONDON": "XLON", "LON": "XLON",
    "TSE": "XTKS", "TOKYO": "XTKS", "JPX": "XTKS",
    "HKSE": "XHKG", "HKG": "XHKG", "HONG KONG": "XHKG",
    "XETRA": "XETR", "GER": "XETR", "FRANKFURT": "XETR", "FRA": "XETR",
    "PARIS": "XPAR", "EURONEXT PARIS": "XPAR",
    "AMSTERDAM": "XAMS", "TORONTO": "XTSE", "TSX": "XTSE", "TOR": "XTSE",
    "ASX": "XASX", "AUSTRALIA": "XASX",
    "SWISS": "XSWX", "SIX": "XSWX", "EBS": "XSWX",
    "MILAN": "XMIL", "MADRID": "XMAD", "STOCKHOLM": "XSTO",
    "NSE": "XNSE", "NSI": "XNSE", "BSE": "XBOM", "BOM": "XBOM",
    "KRX": "XKRX", "KOSPI": "XKRX", "TAIWAN": "XTAI", "TWO": "XTAI",
    "SHANGHAI": "XSHG", "SHENZHEN": "XSHE", "SAO PAULO": "XSAO", "B3": "XSAO",
    "JOHANNESBURG": "XJSE", "JSE": "XJSE",
}


def resolve(raw: str) -> tuple[str, dict]:
    """Resolve an exchange string (MIC / friendly name / alias / Yahoo code) to
    (MIC, metadata). Unknown exchanges fall through to a tier-3 passthrough so a
    narrative can still be created about the equity — it just won't get a price."""
    key = (raw or "").strip().upper()
    mic = key if key in EXCHANGES else ALIASES.get(key)
    if mic and mic in EXCHANGES:
        return mic, EXCHANGES[mic]
    return key, {"name": raw.strip(), "yahoo": None, "currency": None, "country": None, "tier": 3}


def meta(mic: str) -> dict:
    """Metadata for a MIC (tier-3 passthrough if we don't know it)."""
    return EXCHANGES.get(mic, {"name": mic, "yahoo": None, "currency": None, "country": None, "tier": 3})


def yahoo_symbol(ticker: str, mic: str) -> str | None:
    """Translate (ticker, MIC) into Yahoo's symbol, or None if we have no free
    price source for that exchange (tier 3 / unknown). Yahoo uses '-' for the
    class-share separator (BRK.B -> BRK-B) and a suffix for non-US listings."""
    m = EXCHANGES.get(mic)
    if m is None or m.get("yahoo") is None:
        return None
    base = ticker.strip().upper().replace(".", "-")
    suffix = m["yahoo"]
    return f"{base}.{suffix}" if suffix else base

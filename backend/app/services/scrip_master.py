"""Angel One instrument ("scrip") master loader.

Angel publishes the full instrument list as a single JSON file. We fetch it
once, cache it in-process for the day, and use it to resolve index tokens and
to enumerate option contracts for a given index + nearest expiry.

Everything here is best-effort: callers must handle a None / empty return and
fall back to synthetic data (the network call may fail, the format may drift,
or the process may be offline).
"""
from __future__ import annotations

import time
from datetime import datetime

import httpx

SCRIP_URL = (
    "https://margincalculator.angelbroking.com/OpenAPI_File/files/"
    "OpenAPIScripMaster.json"
)

# Well-known spot-index tokens (NSE unless noted). Used directly for quotes so
# we don't need the (large) scrip master just to read the five headline indices.
INDEX_TOKENS: dict[str, dict] = {
    "NIFTY": {"exchange": "NSE", "token": "26000", "name": "Nifty 50"},
    "BANKNIFTY": {"exchange": "NSE", "token": "26009", "name": "Nifty Bank"},
    "FINNIFTY": {"exchange": "NSE", "token": "26037", "name": "Nifty Fin Service"},
    "MIDCPNIFTY": {"exchange": "NSE", "token": "26074", "name": "Nifty Midcap Select"},
    "SENSEX": {"exchange": "BSE", "token": "99919000", "name": "Sensex"},
}
VIX_TOKEN = {"exchange": "NSE", "token": "26017", "name": "India VIX"}

# Option underlying "name" field in the scrip master keyed by our symbol.
OPTION_NAME = {
    "NIFTY": "NIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "FINNIFTY": "FINNIFTY",
    "MIDCPNIFTY": "MIDCPNIFTY",
    "SENSEX": "SENSEX",
}

_cache: dict = {"day": None, "rows": None}


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_master(timeout: float = 15.0) -> list[dict] | None:
    """Return the parsed scrip master (cached per calendar day)."""
    if _cache["rows"] is not None and _cache["day"] == _today():
        return _cache["rows"]
    try:
        resp = httpx.get(SCRIP_URL, timeout=timeout)
        resp.raise_for_status()
        rows = resp.json()
        _cache.update(day=_today(), rows=rows)
        return rows
    except Exception:
        return None


# A liquid large-cap universe for computing gainers/losers & breadth.
# (Angel getMarketData accepts up to ~50 tokens per call.)
NIFTY_UNIVERSE = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "BHARTIARTL",
    "ITC", "LT", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "BAJFINANCE", "MARUTI",
    "SUNPHARMA", "TATAMOTORS", "NTPC", "POWERGRID", "TITAN", "ULTRACEMCO",
    "ASIANPAINT", "WIPRO", "HCLTECH", "ADANIENT", "TATASTEEL", "JSWSTEEL",
    "M&M", "NESTLEIND", "BAJAJFINSV", "TECHM",
]


def equity_tokens(symbols: list[str], rows: list[dict] | None = None) -> dict[str, str]:
    """Resolve NSE cash-segment tokens for plain equity symbols.

    Matches rows whose tradingsymbol is '<SYMBOL>-EQ' on the NSE segment.
    Returns {symbol: token}. Pure given `rows`."""
    rows = rows if rows is not None else load_master()
    if not rows:
        return {}
    wanted = {s.upper() for s in symbols}
    out: dict[str, str] = {}
    for r in rows:
        sym = (r.get("symbol") or "").upper()
        if r.get("exch_seg") != "NSE" or not sym.endswith("-EQ"):
            continue
        base = sym[:-3]
        if base in wanted and base not in out:
            out[base] = r.get("token")
    return out


def _parse_expiry(value: str):
    # Scrip-master expiry looks like "25JAN2024".
    for fmt in ("%d%b%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value.upper(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def option_chain_instruments(
    symbol: str, rows: list[dict] | None = None
) -> tuple[str | None, list[dict]]:
    """Return (expiry_label, instruments) for the *nearest* expiry of an index.

    Each instrument dict carries token / strike / option type (CE/PE).
    Pure given `rows`, so it is unit-testable with a sample master.
    """
    rows = rows if rows is not None else load_master()
    if not rows:
        return None, []

    name = OPTION_NAME.get(symbol, symbol)
    opts = [
        r
        for r in rows
        if r.get("name") == name
        and r.get("instrumenttype") in ("OPTIDX", "OPTIDX ")
        and r.get("symbol", "").endswith(("CE", "PE"))
    ]
    if not opts:
        return None, []

    # Pick the soonest expiry that is not in the past.
    today = datetime.now()
    dated = []
    for r in opts:
        exp = _parse_expiry(r.get("expiry", ""))
        if exp and exp >= today.replace(hour=0, minute=0, second=0, microsecond=0):
            dated.append((exp, r))
    if not dated:
        return None, []

    nearest = min(d[0] for d in dated)
    chosen = [r for exp, r in dated if exp == nearest]

    instruments = []
    for r in chosen:
        try:
            strike = int(float(r["strike"]) / 100)  # master stores strike*100
        except (KeyError, ValueError, TypeError):
            continue
        instruments.append(
            {
                "token": r.get("token"),
                "strike": strike,
                "type": "CE" if r["symbol"].endswith("CE") else "PE",
                "tradingsymbol": r.get("symbol"),
                "exchange": r.get("exch_seg", "NFO"),
            }
        )
    return nearest.strftime("%d %b %Y"), instruments

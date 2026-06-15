"""Free, no-auth market data via Yahoo Finance.

Used as the data source when Angel One credentials are absent, so the app
shows *real* index quotes and candles without any API key. Yahoo has no Indian
option chain, so OI stays synthetic. All network calls are best-effort and the
caller falls back to the deterministic mock on any failure.
"""
from __future__ import annotations

import time

import httpx

from . import live_transforms

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockLens/1.0)"}
_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

# Our symbol -> Yahoo ticker. The first three are reliable; the last two are
# best-effort (callers fill any gap from mock).
YF_SYMBOL = {
    "NIFTY": "%5ENSEI",
    "BANKNIFTY": "%5ENSEBANK",
    "SENSEX": "%5EBSESN",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "MIDCPNIFTY": "%5ENSEMDCP50",
}
YF_VIX = "%5EINDIAVIX"

# timeframe -> (Yahoo interval, range, resample mode)
INTERVAL = {
    "1H": ("1h", "1mo", None),
    "4H": ("1h", "3mo", "x4"),
    "1D": ("1d", "1y", None),
    "1W": ("1wk", "2y", None),
}

# Tiny in-process cache so repeated page loads don't hammer Yahoo.
_TTL = 30
_cache: dict[str, tuple] = {}


def _get(symbol_yf: str, interval: str, rng: str, timeout: float = 5.0) -> dict:
    key = f"{symbol_yf}:{interval}:{rng}"
    hit = _cache.get(key)
    now = time.time()
    if hit and hit[1] > now:
        return hit[0]
    resp = httpx.get(
        _BASE.format(symbol=symbol_yf),
        params={"interval": interval, "range": rng},
        headers=_HEADERS,
        timeout=timeout,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    _cache[key] = (result, now + _TTL)
    return result


# ---- pure parsers (unit-testable) ----
def parse_quote(symbol: str, label: str, result: dict) -> dict | None:
    meta = result.get("meta", {})
    ltp = meta.get("regularMarketPrice")
    # previousClose = prior session's close (correct for daily % change);
    # chartPreviousClose depends on the requested range, so prefer previousClose.
    prev = meta.get("previousClose") or meta.get("chartPreviousClose")
    if ltp is None or not prev:
        return None
    change = ltp - prev
    return {
        "symbol": symbol,
        "label": label,
        "ltp": round(float(ltp), 2),
        "change": round(float(change), 2),
        "changePct": round(float(change) / prev * 100, 2),
    }


def parse_candles(result: dict) -> list[dict]:
    ts = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    o, h, l, c = (quote.get(k) or [] for k in ("open", "high", "low", "close"))
    out = []
    for i, t in enumerate(ts):
        try:
            vo, vh, vl, vc = o[i], h[i], l[i], c[i]
        except IndexError:
            continue
        if None in (vo, vh, vl, vc):
            continue
        out.append(
            {"time": int(t), "open": round(vo, 2), "high": round(vh, 2),
             "low": round(vl, 2), "close": round(vc, 2)}
        )
    out.sort(key=lambda x: x["time"])
    return out


# ---- network-backed fetchers (best-effort) ----
def fetch_index_quotes(labels: dict[str, str]) -> tuple[dict[str, dict], float | None]:
    """Return ({symbol: quote} for whatever resolved, vix_or_None)."""
    quotes: dict[str, dict] = {}
    for sym, yf in YF_SYMBOL.items():
        try:
            q = parse_quote(sym, labels.get(sym, sym), _get(yf, "1d", "1d"))
            if q:
                quotes[sym] = q
        except Exception:
            continue
    vix = None
    try:
        meta = _get(YF_VIX, "1d", "1d").get("meta", {})
        if meta.get("regularMarketPrice") is not None:
            vix = round(float(meta["regularMarketPrice"]), 2)
    except Exception:
        vix = None
    return quotes, vix


def fetch_vix() -> float | None:
    """India VIX via Yahoo (^INDIAVIX) — reliable free fallback."""
    try:
        meta = _get(YF_VIX, "1d", "1d").get("meta", {})
        v = meta.get("regularMarketPrice")
        return round(float(v), 2) if v else None
    except Exception:
        return None


def fetch_candles(symbol: str, timeframe: str) -> list[dict]:
    yf = YF_SYMBOL.get(symbol)
    if not yf:
        raise RuntimeError(f"no Yahoo ticker for {symbol}")
    interval, rng, mode = INTERVAL.get(timeframe, ("1d", "1y", None))
    candles = parse_candles(_get(yf, interval, rng))
    if not candles:
        raise RuntimeError("empty Yahoo candles")
    return live_transforms.resample(candles, mode)

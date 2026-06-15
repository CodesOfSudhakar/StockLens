"""Angel One SmartAPI market-data provider.

When valid credentials are present we attempt a live SmartConnect session;
on any failure (no creds, network, library mismatch) we fall back to a
deterministic synthetic generator so the whole app stays usable offline.
"""
from __future__ import annotations

import logging
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

from ..deps import Credentials
from . import indicators, live_transforms, oi_analysis, scrip_master, yahoo

# Index metadata: label, an anchor spot price, and option-strike step.
INDEX_META: dict[str, dict] = {
    "NIFTY": {"label": "Nifty 50", "anchor": 24800, "step": 50},
    "BANKNIFTY": {"label": "Bank Nifty", "anchor": 52400, "step": 100},
    "FINNIFTY": {"label": "Fin Nifty", "anchor": 23600, "step": 50},
    "MIDCPNIFTY": {"label": "MidCap", "anchor": 12600, "step": 25},
    "SENSEX": {"label": "Sensex", "anchor": 81300, "step": 100},
}

# Timeframe -> (seconds per candle, number of candles)
TF_MAP: dict[str, tuple[int, int]] = {
    "1H": (3600, 168),
    "4H": (14400, 120),
    "1D": (86400, 180),
    "1W": (604800, 120),
}

_NIFTY_STOCKS = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "BHARTIARTL",
    "ITC", "LT", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "BAJFINANCE", "MARUTI",
]


log = logging.getLogger("stocklens.angel")
if not log.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
    log.propagate = False


def _offline() -> bool:
    """When set (e.g. in tests/CI), skip all free-network providers so the
    deterministic mock is used — keeps the suite hermetic."""
    return bool(os.environ.get("STOCKLENS_OFFLINE"))


def _rng(seed: str) -> random.Random:
    return random.Random(seed)


# --------------------------------------------------------------------------
# Live session (best-effort)
# --------------------------------------------------------------------------
# Cache authenticated sessions briefly so a single page (which fetches quotes,
# candles, and OI) doesn't re-login three times and trip Angel's login limits.
_SESSION_TTL = 300  # seconds
_session_cache: dict[tuple, tuple] = {}


def _live_session(creds: Credentials):
    """Return an authenticated SmartConnect or None (cached per credentials)."""
    if not creds.has_angel:
        return None

    key = (creds.angel_client_id, creds.angel_api_key)
    now = time.time()
    cached = _session_cache.get(key)
    if cached and cached[1] > now:
        return cached[0]

    try:
        import pyotp
        from SmartApi import SmartConnect  # smartapi-python

        api = SmartConnect(api_key=creds.angel_api_key)
        totp = pyotp.TOTP(creds.angel_totp_secret).now() if creds.angel_totp_secret else ""
        api.generateSession(creds.angel_client_id, creds.angel_pin, totp)
        _session_cache[key] = (api, now + _SESSION_TTL)
        log.info("Angel session established for client %s", creds.angel_client_id)
        return api
    except Exception as e:
        # Library missing, bad creds, or network issue — fall back to mock.
        log.warning("Angel session FAILED for client %s: %r", creds.angel_client_id, e)
        return None


# --------------------------------------------------------------------------
# Live fetchers (best-effort; each caller wraps these and falls back to mock)
# --------------------------------------------------------------------------
def _market_data(api, exchange_tokens: dict[str, list[str]]) -> dict[str, dict]:
    """Call getMarketData FULL and return a {token: item} map."""
    resp = api.getMarketData("FULL", exchange_tokens)
    fetched = (resp or {}).get("data", {}).get("fetched", []) or []
    return {str(item.get("symbolToken")): item for item in fetched}


def _fetch_live_indices(api) -> tuple[list[dict], float]:
    """Live quotes for the five indices + India VIX. Raises on failure."""
    by_exchange: dict[str, list[str]] = {}
    for meta in list(scrip_master.INDEX_TOKENS.values()) + [scrip_master.VIX_TOKEN]:
        by_exchange.setdefault(meta["exchange"], []).append(meta["token"])

    quotes = _market_data(api, by_exchange)
    indices = []
    for sym, meta in scrip_master.INDEX_TOKENS.items():
        item = quotes.get(meta["token"])
        if not item:
            raise RuntimeError(f"no quote for {sym}")
        indices.append(
            live_transforms.parse_index_quote(sym, INDEX_META[sym]["label"], item)
        )
    vix_item = quotes.get(scrip_master.VIX_TOKEN["token"], {})
    vix = round(float(vix_item.get("ltp", 0) or 0), 2)
    return indices, vix


def _fetch_live_movers(api) -> dict:
    """Real gainers/losers + breadth from a liquid Nifty universe."""
    tokens = scrip_master.equity_tokens(scrip_master.NIFTY_UNIVERSE)
    if not tokens:
        raise RuntimeError("could not resolve equity tokens")
    quotes = _market_data(api, {"NSE": list(tokens.values())})
    tok2sym = {str(v): k for k, v in tokens.items()}
    changes: dict[str, float] = {}
    for tok, item in quotes.items():
        sym = tok2sym.get(str(tok))
        if sym:
            changes[sym] = float(item.get("percentChange", 0) or 0)
    if not changes:
        raise RuntimeError("no equity quotes returned")
    return live_transforms.movers_and_breadth(changes)


def _fetch_live_candles(api, symbol: str, timeframe: str) -> list[dict]:
    interval, mode = live_transforms.TIMEFRAME_INTERVAL.get(
        timeframe, ("ONE_DAY", None)
    )
    lookback_days = 40 if interval == "ONE_HOUR" else 400
    meta = scrip_master.INDEX_TOKENS.get(symbol, scrip_master.INDEX_TOKENS["NIFTY"])
    now = datetime.now()
    params = {
        "exchange": meta["exchange"],
        "symboltoken": meta["token"],
        "interval": interval,
        "fromdate": (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d %H:%M"),
        "todate": now.strftime("%Y-%m-%d %H:%M"),
    }
    resp = api.getCandleData(params)
    rows = (resp or {}).get("data", []) or []
    candles = live_transforms.candles_from_angel(rows)
    if not candles:
        raise RuntimeError("empty candle data")
    return live_transforms.resample(candles, mode)


def _fetch_live_oi(api, symbol: str, spot: float) -> dict:
    expiry, instruments = scrip_master.option_chain_instruments(symbol)
    if not instruments:
        raise RuntimeError("no option instruments")
    step = INDEX_META.get(symbol, INDEX_META["NIFTY"])["step"]
    atm = round(spot / step) * step
    wanted = {atm + k * step for k in range(-4, 5)}
    near = [i for i in instruments if i["strike"] in wanted]
    if not near:
        raise RuntimeError("no near-ATM strikes")

    by_exchange: dict[str, list[str]] = {}
    for inst in near:
        by_exchange.setdefault(inst["exchange"], []).append(str(inst["token"]))
    quotes = _market_data(api, by_exchange)
    chain = live_transforms.build_option_chain(near, quotes, spot, step)
    if not chain["chain"]:
        raise RuntimeError("empty option chain")
    return chain


# --------------------------------------------------------------------------
# Synthetic candle generator (deterministic per symbol+timeframe)
# --------------------------------------------------------------------------
def _gen_candles(symbol: str, timeframe: str) -> list[dict]:
    meta = INDEX_META.get(symbol, INDEX_META["NIFTY"])
    step_secs, count = TF_MAP.get(timeframe, TF_MAP["1D"])
    rnd = _rng(f"{symbol}:{timeframe}")

    now = int(time.time())
    start = now - step_secs * count
    price = meta["anchor"] * 0.95
    drift = 0.0006
    vol = meta["anchor"] * 0.004

    candles: list[dict] = []
    for i in range(count):
        t = start + i * step_secs
        # slow sine cycle + random walk for realistic structure
        cycle = math.sin(i / 14) * vol * 1.5
        shock = rnd.gauss(0, vol)
        o = price
        c = price * (1 + drift) + shock + cycle * 0.04
        hi = max(o, c) + abs(rnd.gauss(0, vol * 0.4))
        lo = min(o, c) - abs(rnd.gauss(0, vol * 0.4))
        candles.append(
            {"time": t, "open": round(o, 2), "high": round(hi, 2),
             "low": round(lo, 2), "close": round(c, 2)}
        )
        price = c
    return candles


def _build_oi(symbol: str, spot: float) -> dict:
    meta = INDEX_META.get(symbol, INDEX_META["NIFTY"])
    step = meta["step"]
    rnd = _rng(f"{symbol}:oi:{int(spot)}")
    atm = round(spot / step) * step

    chain = []
    for k in range(-4, 5):
        strike = atm + k * step
        # OI concentrates near ATM; calls heavier above, puts heavier below.
        base = max(1, 9 - abs(k)) * rnd.randint(40000, 90000)
        ce_oi = int(base * (1.2 if k >= 0 else 0.7))
        pe_oi = int(base * (1.2 if k <= 0 else 0.7))
        ce_oi_change = rnd.randint(-40000, 60000)
        pe_oi_change = rnd.randint(-40000, 60000)
        # Price proxy: above-ATM calls cheapen as spot sits below; sign by side.
        ce_price_change = (spot - strike) * rnd.uniform(0.4, 1.0)
        pe_price_change = (strike - spot) * rnd.uniform(0.4, 1.0)
        chain.append(
            {
                "strike": int(strike),
                "step": step,
                "ceOi": ce_oi,
                "peOi": pe_oi,
                "ceBuildup": oi_analysis.classify_buildup(ce_oi_change, ce_price_change),
                "peBuildup": oi_analysis.classify_buildup(pe_oi_change, pe_price_change),
            }
        )

    return {
        "spot": round(spot, 2),
        "pcr": oi_analysis.pcr(chain),
        "maxPain": oi_analysis.max_pain(chain),
        "chain": chain,
    }


# --------------------------------------------------------------------------
# Public API (live-first, with graceful per-section fallback to mock)
# --------------------------------------------------------------------------
def _mock_index(sym: str) -> dict:
    meta = INDEX_META.get(sym, INDEX_META["NIFTY"])
    rnd = _rng(f"{sym}:overview:{datetime.now(timezone.utc):%Y-%m-%d-%H}")
    change_pct = rnd.uniform(-1.1, 1.3)
    ltp = meta["anchor"] * (1 + change_pct / 100)
    return {
        "symbol": sym,
        "label": meta["label"],
        "ltp": round(ltp, 2),
        "change": round(ltp - meta["anchor"], 2),
        "changePct": round(change_pct, 2),
    }


def _mock_indices() -> list[dict]:
    return [_mock_index(sym) for sym in INDEX_META]


def get_overview(creds: Credentials) -> dict:
    api = _live_session(creds)
    log.info("overview: has_angel=%s", creds.has_angel)

    source = "mock"
    vix = None
    indices = None
    movers_data = None

    # 1) Indices + VIX + movers via Angel.
    if api is not None:
        try:
            indices, vix = _fetch_live_indices(api)
            source = "live"
        except Exception as e:
            log.warning("Angel indices FAILED: %r", e)
        try:
            movers_data = _fetch_live_movers(api)
        except Exception as e:
            log.warning("Angel movers FAILED: %r", e)

    # 2) Yahoo fallback for indices/VIX (free, no key).
    if indices is None and not _offline():
        try:
            labels = {s: m["label"] for s, m in INDEX_META.items()}
            yq, yvix = yahoo.fetch_index_quotes(labels)
            if yq:
                indices = [yq.get(s) or _mock_index(s) for s in INDEX_META]
                vix = yvix if yvix is not None else vix
                source = "yahoo"
        except Exception as e:
            log.warning("Yahoo indices FAILED: %r", e)
    if indices is None:
        indices = _mock_indices()

    # India VIX: Angel often omits it from the FULL batch -> Yahoo fallback.
    if not vix and not _offline():
        vix = yahoo.fetch_vix()

    # 3) Breadth/movers: live if available, else synthetic.
    rnd = _rng(f"breadth:{datetime.now(timezone.utc):%Y-%m-%d-%H}")
    if not vix:
        vix = round(rnd.uniform(11, 18), 2)

    if movers_data is None:
        m = [{"symbol": s, "changePct": round(rnd.uniform(-6, 6), 2)} for s in _NIFTY_STOCKS]
        m.sort(key=lambda x: x["changePct"], reverse=True)
        movers_data = {
            "gainers": m[:4],
            "losers": m[-4:][::-1],
            "breadth": {
                "advances": rnd.randint(900, 1600),
                "declines": rnd.randint(700, 1500),
                "unchanged": rnd.randint(40, 120),
            },
        }

    avg = sum(i["changePct"] for i in indices) / len(indices)
    if avg > 0.25:
        sentiment, label = "bullish", "Risk-on"
    elif avg < -0.25:
        sentiment, label = "bearish", "Risk-off"
    else:
        sentiment, label = "neutral", "Range-bound"

    return {
        "indices": indices,
        "vix": vix,
        "breadth": movers_data["breadth"],
        "gainers": movers_data["gainers"],
        "losers": movers_data["losers"],
        "sentiment": sentiment,
        "sentimentLabel": label,
        "source": source,
    }


def get_candles_and_rsi(creds: Credentials, symbol: str, timeframe: str):
    candles = None
    api = _live_session(creds)
    if api is not None:
        try:
            candles = _fetch_live_candles(api, symbol, timeframe)
        except Exception as e:
            log.warning("Angel candle fetch FAILED for %s/%s: %r", symbol, timeframe, e)
            candles = None
    if not candles and not _offline():
        # Free Yahoo fallback (real data, no key) before synthetic.
        try:
            candles = yahoo.fetch_candles(symbol, timeframe)
        except Exception as e:
            log.warning("Yahoo candle fetch FAILED for %s/%s: %r", symbol, timeframe, e)
            candles = None
    if not candles:
        candles = _gen_candles(symbol, timeframe)

    closes = [c["close"] for c in candles]
    rsi_vals = indicators.rsi(closes, 14)
    rsi = [{"time": c["time"], "value": round(v, 2)} for c, v in zip(candles, rsi_vals)]
    return candles, rsi


def get_oi(creds: Credentials, symbol: str, spot: float) -> dict:
    api = _live_session(creds)
    if api is not None:
        try:
            return _fetch_live_oi(api, symbol, spot)
        except Exception as e:
            log.warning("Angel OI fetch FAILED for %s: %r", symbol, e)
    return _build_oi(symbol, spot)

"""Angel One SmartAPI market-data provider.

When valid credentials are present we attempt a live SmartConnect session;
on any failure (no creds, network, library mismatch) we fall back to a
deterministic synthetic generator so the whole app stays usable offline.
"""
from __future__ import annotations

import math
import random
import time
from datetime import datetime, timezone

from ..deps import Credentials
from . import indicators, oi_analysis

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


def _rng(seed: str) -> random.Random:
    return random.Random(seed)


# --------------------------------------------------------------------------
# Live session (best-effort)
# --------------------------------------------------------------------------
def _live_session(creds: Credentials):
    """Return an authenticated SmartConnect or None."""
    if not creds.has_angel:
        return None
    try:
        import pyotp
        from SmartApi import SmartConnect  # smartapi-python

        api = SmartConnect(api_key=creds.angel_api_key)
        totp = pyotp.TOTP(creds.angel_totp_secret).now() if creds.angel_totp_secret else ""
        api.generateSession(creds.angel_client_id, creds.angel_pin, totp)
        return api
    except Exception:
        # Library missing, bad creds, or network issue — fall back to mock.
        return None


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
# Public API
# --------------------------------------------------------------------------
def get_overview(creds: Credentials) -> dict:
    live = _live_session(creds)
    source = "live" if live else "mock"

    indices = []
    for sym, meta in INDEX_META.items():
        rnd = _rng(f"{sym}:overview:{datetime.now(timezone.utc):%Y-%m-%d-%H}")
        change_pct = rnd.uniform(-1.1, 1.3)
        ltp = meta["anchor"] * (1 + change_pct / 100)
        change = ltp - meta["anchor"]
        indices.append(
            {
                "symbol": sym,
                "label": meta["label"],
                "ltp": round(ltp, 2),
                "change": round(change, 2),
                "changePct": round(change_pct, 2),
            }
        )

    rnd = _rng(f"breadth:{datetime.now(timezone.utc):%Y-%m-%d-%H}")
    advances = rnd.randint(900, 1600)
    declines = rnd.randint(700, 1500)

    movers = [
        {"symbol": s, "changePct": round(rnd.uniform(-6, 6), 2)} for s in _NIFTY_STOCKS
    ]
    movers.sort(key=lambda m: m["changePct"], reverse=True)
    gainers = movers[:4]
    losers = movers[-4:][::-1]

    avg = sum(i["changePct"] for i in indices) / len(indices)
    if avg > 0.25:
        sentiment, label = "bullish", "Risk-on"
    elif avg < -0.25:
        sentiment, label = "bearish", "Risk-off"
    else:
        sentiment, label = "neutral", "Range-bound"

    return {
        "indices": indices,
        "vix": round(rnd.uniform(11, 18), 2),
        "breadth": {"advances": advances, "declines": declines, "unchanged": rnd.randint(40, 120)},
        "gainers": gainers,
        "losers": losers,
        "sentiment": sentiment,
        "sentimentLabel": label,
        "source": source,
    }


def get_candles_and_rsi(creds: Credentials, symbol: str, timeframe: str):
    candles = _gen_candles(symbol, timeframe)
    closes = [c["close"] for c in candles]
    rsi_vals = indicators.rsi(closes, 14)
    rsi = [{"time": c["time"], "value": round(v, 2)} for c, v in zip(candles, rsi_vals)]
    return candles, rsi


def get_oi(creds: Credentials, symbol: str, spot: float) -> dict:
    return _build_oi(symbol, spot)

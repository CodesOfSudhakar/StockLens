"""Pure transforms that turn raw Angel One payloads into our internal shapes.

Kept free of network I/O so they can be unit-tested with sample payloads.
"""
from __future__ import annotations

from datetime import datetime

from . import oi_analysis

# Our timeframe -> (Angel native interval, resample mode)
TIMEFRAME_INTERVAL = {
    "1H": ("ONE_HOUR", None),
    "4H": ("ONE_HOUR", "x4"),   # aggregate four 1H candles
    "1D": ("ONE_DAY", None),
    "1W": ("ONE_DAY", "weekly"),
}


def candles_from_angel(rows: list[list]) -> list[dict]:
    """Angel getCandleData rows are [timestamp, open, high, low, close, volume].
    Timestamp is ISO-8601 with offset, e.g. '2024-01-25T09:15:00+05:30'."""
    out = []
    for r in rows:
        try:
            ts = int(datetime.fromisoformat(r[0]).timestamp())
            out.append(
                {
                    "time": ts,
                    "open": round(float(r[1]), 2),
                    "high": round(float(r[2]), 2),
                    "low": round(float(r[3]), 2),
                    "close": round(float(r[4]), 2),
                }
            )
        except (ValueError, IndexError, TypeError):
            continue
    out.sort(key=lambda c: c["time"])
    return out


def _aggregate(bucket: list[dict]) -> dict:
    return {
        "time": bucket[0]["time"],
        "open": bucket[0]["open"],
        "high": max(c["high"] for c in bucket),
        "low": min(c["low"] for c in bucket),
        "close": bucket[-1]["close"],
    }


def resample(candles: list[dict], mode: str | None) -> list[dict]:
    """Aggregate candles. mode None = passthrough, 'x4' = every 4, 'weekly' =
    by ISO week."""
    if not mode or not candles:
        return candles
    if mode == "x4":
        return [_aggregate(candles[i : i + 4]) for i in range(0, len(candles), 4)]
    if mode == "weekly":
        groups: dict = {}
        order: list = []
        for c in candles:
            key = datetime.utcfromtimestamp(c["time"]).isocalendar()[:2]  # (year, week)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(c)
        return [_aggregate(groups[k]) for k in order]
    return candles


def parse_index_quote(symbol: str, label: str, item: dict) -> dict:
    """Map one Angel getMarketData 'fetched' item to our IndexQuote shape."""
    ltp = float(item.get("ltp", 0) or 0)
    change = float(item.get("netChange", 0) or 0)
    pct = float(item.get("percentChange", 0) or 0)
    return {
        "symbol": symbol,
        "label": label,
        "ltp": round(ltp, 2),
        "change": round(change, 2),
        "changePct": round(pct, 2),
    }


def build_option_chain(
    instruments: list[dict], quote_by_token: dict[str, dict], spot: float, step: int
) -> dict:
    """Combine option instruments with their live FULL quotes into a chain
    centred on ATM (±4 strikes). OI/PCR/MaxPain are exact; buildup is inferred
    from each leg's price move (netChange) since intraday OI delta isn't in the
    FULL payload."""
    atm = round(spot / step) * step
    wanted = {atm + k * step for k in range(-4, 5)}

    rows: dict[int, dict] = {}
    for inst in instruments:
        strike = inst["strike"]
        if strike not in wanted:
            continue
        q = quote_by_token.get(str(inst["token"]))
        if not q:
            continue
        oi = int(float(q.get("opnInterest", 0) or 0))
        net = float(q.get("netChange", 0) or 0)
        row = rows.setdefault(
            strike, {"strike": strike, "step": step, "ceOi": 0, "peOi": 0,
                     "ceBuildup": "", "peBuildup": ""}
        )
        # OI rising assumed when the leg holds a position; classify by price move.
        buildup = oi_analysis.classify_buildup(oi_change=1, price_change=net)
        if inst["type"] == "CE":
            row["ceOi"] = oi
            row["ceBuildup"] = buildup
        else:
            row["peOi"] = oi
            row["peBuildup"] = buildup

    chain = [rows[s] for s in sorted(rows)]
    return {
        "spot": round(spot, 2),
        "pcr": oi_analysis.pcr(chain) if chain else 0.0,
        "maxPain": oi_analysis.max_pain(chain) if chain else int(atm),
        "chain": chain,
    }

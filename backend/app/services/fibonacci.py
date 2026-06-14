"""Fibonacci retracement & extension levels from the dominant swing."""
from __future__ import annotations

RETRACEMENTS = [0.236, 0.382, 0.5, 0.618, 0.786]
EXTENSIONS = [1.272, 1.618, 2.0]


def _swing(candles: list[dict], lookback: int):
    """Identify the swing high/low (and their order) over the last `lookback`
    candles."""
    window = candles[-lookback:] if lookback else candles
    hi_idx = max(range(len(window)), key=lambda i: window[i]["high"])
    lo_idx = min(range(len(window)), key=lambda i: window[i]["low"])
    high = window[hi_idx]["high"]
    low = window[lo_idx]["low"]
    # If the high came after the low, the dominant leg is up.
    direction = "up" if hi_idx >= lo_idx else "down"
    return high, low, direction


def levels(candles: list[dict], lookback: int = 90) -> dict | None:
    """Return Fibonacci levels for the dominant swing, or None if not enough
    data / a degenerate (flat) range."""
    if len(candles) < 5:
        return None
    high, low, direction = _swing(candles, lookback)
    diff = high - low
    if diff <= 0:
        return None

    out = []
    for r in RETRACEMENTS:
        price = high - diff * r if direction == "up" else low + diff * r
        out.append({"ratio": r, "price": round(price, 2), "kind": "retracement"})
    for r in EXTENSIONS:
        # Project beyond the swing in the direction of the move.
        price = high + diff * (r - 1) if direction == "up" else low - diff * (r - 1)
        out.append({"ratio": r, "price": round(price, 2), "kind": "extension"})

    # Anchor levels (0% and 100%) for reference.
    out.insert(0, {"ratio": 0.0, "price": round(high if direction == "up" else low, 2), "kind": "anchor"})
    out.append({"ratio": 1.0, "price": round(low if direction == "up" else high, 2), "kind": "anchor"})

    return {
        "high": round(high, 2),
        "low": round(low, 2),
        "direction": direction,
        "levels": out,
    }

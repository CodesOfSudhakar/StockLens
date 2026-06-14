"""Harmonic pattern detection (Gartley / Bat / Butterfly / Crab).

A zigzag picks out alternating swing pivots; the last five (X-A-B-C-D) are
tested against each pattern's Fibonacci ratio rules with a tolerance band.
Pure math — testable with synthetic XABCD price paths.
"""
from __future__ import annotations

# Each pattern: AB/XA, BC/AB, CD/BC, AD/XA ranges.
PATTERNS = {
    "Gartley": {"AB_XA": (0.55, 0.68), "BC_AB": (0.382, 0.886), "CD_BC": (1.13, 1.618), "AD_XA": (0.74, 0.83)},
    "Bat": {"AB_XA": (0.382, 0.5), "BC_AB": (0.382, 0.886), "CD_BC": (1.618, 2.618), "AD_XA": (0.85, 0.92)},
    "Butterfly": {"AB_XA": (0.74, 0.83), "BC_AB": (0.382, 0.886), "CD_BC": (1.618, 2.24), "AD_XA": (1.27, 1.618)},
    "Crab": {"AB_XA": (0.382, 0.618), "BC_AB": (0.382, 0.886), "CD_BC": (2.0, 3.618), "AD_XA": (1.55, 1.68)},
}


def zigzag(candles: list[dict], pct: float = 0.03) -> list[dict]:
    """Return alternating swing pivots using a percentage reversal threshold."""
    closes = [c["close"] for c in candles]
    if len(closes) < 3:
        return []

    pivots: list[dict] = []
    piv_price, piv_idx, trend = closes[0], 0, 0  # trend: 1 up, -1 down, 0 unset
    for i in range(1, len(closes)):
        change = (closes[i] - piv_price) / piv_price
        if trend >= 0 and change <= -pct:
            pivots.append({"index": piv_idx, "price": piv_price, "type": "H"})
            trend, piv_price, piv_idx = -1, closes[i], i
        elif trend <= 0 and change >= pct:
            pivots.append({"index": piv_idx, "price": piv_price, "type": "L"})
            trend, piv_price, piv_idx = 1, closes[i], i
        elif trend >= 0 and closes[i] > piv_price:
            piv_price, piv_idx = closes[i], i
        elif trend <= 0 and closes[i] < piv_price:
            piv_price, piv_idx = closes[i], i

    pivots.append({"index": piv_idx, "price": piv_price, "type": "H" if trend > 0 else "L"})
    return pivots


def _ratio(a: float, b: float) -> float:
    return abs(a) / abs(b) if b else 0.0


def detect(candles: list[dict], pct: float = 0.03) -> list[dict]:
    """Detect harmonic patterns in the most recent 5 pivots."""
    pivots = zigzag(candles, pct)
    if len(pivots) < 5:
        return []

    X, A, B, C, D = (p["price"] for p in pivots[-5:])
    XA, AB, BC, CD, AD = abs(A - X), abs(B - A), abs(C - B), abs(D - C), abs(D - A)
    if min(XA, AB, BC, CD) == 0:
        return []

    measured = {
        "AB_XA": _ratio(AB, XA),
        "BC_AB": _ratio(BC, AB),
        "CD_BC": _ratio(CD, BC),
        "AD_XA": _ratio(AD, XA),
    }

    found = []
    for name, rules in PATTERNS.items():
        if all(lo <= measured[k] <= hi for k, (lo, hi) in rules.items()):
            d_type = pivots[-1]["type"]
            found.append(
                {
                    "name": name,
                    # D at a low completes a bullish reversal setup, and vice-versa.
                    "direction": "bullish" if d_type == "L" else "bearish",
                    "prz": round(D, 2),  # potential reversal zone (D price)
                    "points": {
                        "X": round(X, 2), "A": round(A, 2), "B": round(B, 2),
                        "C": round(C, 2), "D": round(D, 2),
                    },
                    "ratios": {k: round(v, 3) for k, v in measured.items()},
                }
            )
    return found

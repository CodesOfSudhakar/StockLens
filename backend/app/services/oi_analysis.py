"""Open-interest analytics: buildup classification, PCR, max pain."""
from __future__ import annotations


def classify_buildup(oi_change: float, price_change: float) -> str:
    """Standard four-quadrant OI/price buildup classification.

    price up   + OI up   -> Long Buildup
    price up   + OI down -> Short Covering
    price down + OI down -> Long Unwinding
    price down + OI up   -> Short Buildup
    """
    if price_change >= 0 and oi_change >= 0:
        return "Long Buildup"
    if price_change >= 0 and oi_change < 0:
        return "Short Covering"
    if price_change < 0 and oi_change < 0:
        return "Long Unwinding"
    return "Short Buildup"


def pcr(chain: list[dict]) -> float:
    """Put-Call Ratio by open interest."""
    ce = sum(r["ceOi"] for r in chain)
    pe = sum(r["peOi"] for r in chain)
    return round(pe / ce, 2) if ce else 0.0


def max_pain(chain: list[dict]) -> int:
    """Strike at which total option-writer payout is minimised."""
    strikes = [r["strike"] for r in chain]
    best_strike, best_loss = strikes[0], float("inf")
    for expiry in strikes:
        loss = 0.0
        for r in chain:
            # CE writers lose when expiry > strike; PE writers lose when expiry < strike
            loss += max(expiry - r["strike"], 0) * r["ceOi"]
            loss += max(r["strike"] - expiry, 0) * r["peOi"]
        if loss < best_loss:
            best_loss, best_strike = loss, expiry
    return best_strike


def pcr_signal(value: float) -> tuple[str, str]:
    if value >= 1.2:
        return "bullish", f"PCR {value} (>1.2): heavy put writing — supportive/bullish."
    if value <= 0.8:
        return "bearish", f"PCR {value} (<0.8): heavy call writing — resistance/bearish."
    return "neutral", f"PCR {value}: balanced positioning."

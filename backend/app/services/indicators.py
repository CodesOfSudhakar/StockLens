"""Pure technical-indicator math. No I/O, easy to unit test."""
from __future__ import annotations


def ema(closes: list[float], period: int) -> list[float]:
    if not closes:
        return []
    k = 2 / (period + 1)
    out = [closes[0]]
    for c in closes[1:]:
        out.append(c * k + out[-1] * (1 - k))
    return out


def rsi(closes: list[float], period: int = 14) -> list[float]:
    """Wilder's RSI. Returns a list aligned to `closes` (first `period`
    values are seeded with the running average)."""
    n = len(closes)
    if n < period + 1:
        return [50.0] * n

    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        diff = closes[i] - closes[i - 1]
        gains += max(diff, 0)
        losses += max(-diff, 0)
    avg_gain = gains / period
    avg_loss = losses / period

    out = [50.0] * period
    rs = avg_gain / avg_loss if avg_loss else 100.0
    out.append(100 - 100 / (1 + rs))

    for i in range(period + 1, n):
        diff = closes[i] - closes[i - 1]
        gain = max(diff, 0)
        loss = max(-diff, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        rs = avg_gain / avg_loss if avg_loss else 100.0
        out.append(100 - 100 / (1 + rs))
    return out


def ema_stack_signal(closes: list[float]) -> tuple[str, str]:
    """Classify trend from the EMA 9/26/50/100 stack.
    Returns (signal, human reasoning)."""
    if len(closes) < 100:
        return "neutral", "Insufficient history for a full EMA stack."

    e9 = ema(closes, 9)[-1]
    e26 = ema(closes, 26)[-1]
    e50 = ema(closes, 50)[-1]
    e100 = ema(closes, 100)[-1]
    price = closes[-1]

    bullish_stack = e9 > e26 > e50 > e100
    bearish_stack = e9 < e26 < e50 < e100

    if bullish_stack and price > e9:
        return (
            "bullish",
            f"Price ({price:.0f}) above a rising EMA stack "
            f"(9>{e26:.0f}>26>{e50:.0f}>50>{e100:.0f}) — trend up.",
        )
    if bearish_stack and price < e9:
        return (
            "bearish",
            f"Price ({price:.0f}) below a falling EMA stack — trend down.",
        )
    return (
        "neutral",
        f"EMAs are entangled (9:{e9:.0f} 26:{e26:.0f} 50:{e50:.0f} 100:{e100:.0f}) — no clear trend.",
    )

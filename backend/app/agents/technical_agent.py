"""Technical Agent — reads the EMA stack + RSI and emits a signal."""
from __future__ import annotations

SYSTEM = (
    "You are a disciplined technical analyst for Indian index futures. "
    "Given EMA-stack and RSI facts, state a signal (bullish/bearish/neutral) "
    "and one tight sentence of reasoning. Be specific about levels."
)


def analyze(facts: dict, model) -> dict:
    t = facts["technical"]
    signal = t["signal"]
    heuristic = t["reasoning"]

    if model is None:
        return {"signal": signal, "reasoning": heuristic}

    try:
        prompt = (
            f"{SYSTEM}\n\nSymbol: {facts['symbol']}\n"
            f"Last price: {t['price']:.0f}\n"
            f"EMA9 {t['ema9']:.0f} / EMA26 {t['ema26']:.0f} / "
            f"EMA50 {t['ema50']:.0f} / EMA100 {t['ema100']:.0f}\n"
            f"RSI(14): {t['rsi']:.1f}\n"
            f"Heuristic signal: {signal}.\n"
            "Respond as: SIGNAL: <bullish|bearish|neutral> | REASON: <one sentence>"
        )
        resp = str(model.invoke(prompt).content)
        return _parse(resp, signal, heuristic)
    except Exception:
        return {"signal": signal, "reasoning": heuristic}


def _parse(text: str, fallback_signal: str, fallback_reason: str) -> dict:
    signal, reason = fallback_signal, fallback_reason
    low = text.lower()
    for s in ("bullish", "bearish", "neutral"):
        if s in low.split("reason")[0]:
            signal = s
            break
    if "reason:" in low:
        reason = text.split("REASON:", 1)[-1].split("|")[0].strip() or fallback_reason
    return {"signal": signal, "reasoning": reason}

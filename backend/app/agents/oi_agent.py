"""OI Agent — interprets PCR, Max Pain, and dominant buildups."""
from __future__ import annotations

from .technical_agent import _parse

SYSTEM = (
    "You are an options open-interest specialist for Indian indices. "
    "Given PCR, Max Pain, spot, and buildup counts, give a signal "
    "(bullish/bearish/neutral) and one sentence of reasoning."
)


def analyze(facts: dict, model) -> dict:
    o = facts["oi"]
    signal = o["signal"]
    heuristic = o["reasoning"]

    if model is None:
        return {"signal": signal, "reasoning": heuristic}

    try:
        prompt = (
            f"{SYSTEM}\n\nSymbol: {facts['symbol']}\n"
            f"Spot: {o['spot']:.0f} | Max Pain: {o['maxPain']} | PCR: {o['pcr']}\n"
            f"Buildup tally: {o['buildups']}\n"
            f"Heuristic signal: {signal}.\n"
            "Respond as: SIGNAL: <bullish|bearish|neutral> | REASON: <one sentence>"
        )
        resp = str(model.invoke(prompt).content)
        return _parse(resp, signal, heuristic)
    except Exception:
        return {"signal": signal, "reasoning": heuristic}

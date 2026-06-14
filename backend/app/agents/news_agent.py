"""News Agent — aggregates Groq-tagged headline sentiment."""
from __future__ import annotations

from .technical_agent import _parse

SYSTEM = (
    "You are a market-news analyst. Given recent headline sentiments for an "
    "Indian index, give an overall signal (bullish/bearish/neutral) and one "
    "sentence summarising the news tone."
)


def analyze(facts: dict, model) -> dict:
    n = facts["news"]
    signal = n["signal"]
    heuristic = n["reasoning"]

    if model is None:
        return {"signal": signal, "reasoning": heuristic}

    try:
        headlines = "\n".join(f"- ({it['sentiment']}) {it['title']}" for it in n["items"])
        prompt = (
            f"{SYSTEM}\n\nSymbol: {facts['symbol']}\n"
            f"Headlines:\n{headlines}\n"
            f"Heuristic signal: {signal}.\n"
            "Respond as: SIGNAL: <bullish|bearish|neutral> | REASON: <one sentence>"
        )
        resp = str(model.invoke(prompt).content)
        return _parse(resp, signal, heuristic)
    except Exception:
        return {"signal": signal, "reasoning": heuristic}

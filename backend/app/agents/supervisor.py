"""Supervisor — synthesises the three specialist signals into a final call."""
from __future__ import annotations

import json

_SCORE = {"bullish": 1, "positive": 1, "neutral": 0, "bearish": -1, "negative": -1}

SYSTEM = (
    "You are the supervising portfolio strategist. Three specialist agents "
    "(Technical, OI, News) have each given a signal and reasoning for an Indian "
    "index. Weigh them, resolve conflicts, and produce a single actionable "
    "outlook. Respond ONLY with compact JSON: "
    '{"bias": "...", "range": "...", "keyLevels": "...", "risk": "...", '
    '"confidence": <0-100>, "summary": "..."}'
)


def _heuristic(facts: dict, tech: dict, oi: dict, news: dict) -> dict:
    score = _SCORE.get(tech["signal"], 0) * 1.2
    score += _SCORE.get(oi["signal"], 0)
    score += _SCORE.get(news["signal"], 0) * 0.8

    if score >= 1.2:
        bias = "Bullish"
    elif score <= -1.2:
        bias = "Bearish"
    else:
        bias = "Neutral"

    spot = facts["oi"]["spot"]
    step = facts["oi"]["step"]
    lo = round((spot - step * 3) / step) * step
    hi = round((spot + step * 3) / step) * step
    support = facts["oi"]["maxPain"]
    confidence = int(min(95, 45 + abs(score) * 16))

    return {
        "bias": bias,
        "range": f"{lo:,} – {hi:,}",
        "keyLevels": f"Support {min(support, int(spot)):,} · Resistance {max(support, int(spot)):,}",
        "risk": "Reverse the bias on a sustained close beyond the stated range; "
        "watch India VIX spikes and global cues.",
        "confidence": confidence,
        "summary": (
            f"Technical is {tech['signal']}, OI is {oi['signal']}, news tone is "
            f"{news['signal']}. Net read: {bias.lower()} with {confidence}% conviction."
        ),
    }


def synthesize(facts: dict, tech: dict, oi: dict, news: dict, model) -> dict:
    fallback = _heuristic(facts, tech, oi, news)
    if model is None:
        return fallback

    try:
        prompt = (
            f"{SYSTEM}\n\nSymbol: {facts['symbol']}\n"
            f"Spot: {facts['oi']['spot']:.0f}, strike step: {facts['oi']['step']}\n"
            f"Technical: {tech['signal']} — {tech['reasoning']}\n"
            f"OI: {oi['signal']} — {oi['reasoning']}\n"
            f"News: {news['signal']} — {news['reasoning']}\n"
            f"Max Pain: {facts['oi']['maxPain']}, PCR: {facts['oi']['pcr']}"
        )
        raw = str(model.invoke(prompt).content)
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start : end + 1])
        # backfill any missing keys from the heuristic
        return {**fallback, **{k: v for k, v in data.items() if v not in (None, "")}}
    except Exception:
        return fallback

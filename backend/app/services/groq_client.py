"""Groq access: an LLM factory for the agents and news-sentiment tagging.

Everything degrades gracefully: without a Groq key we keyword-tag sentiment
and the agents run on deterministic heuristics instead of the LLM.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from ..config import get_settings
from ..deps import Credentials

_POSITIVE = {"surge", "rally", "gains", "jumps", "record", "beats", "upgrade",
             "inflows", "profit", "strong", "rises", "boost", "buy"}
_NEGATIVE = {"falls", "slumps", "crash", "drops", "cuts", "downgrade", "outflows",
             "loss", "weak", "selloff", "fears", "miss", "plunge", "warning"}

_HEADLINE_TEMPLATES = [
    ("{sym} extends rally as banking stocks surge on strong inflows", "Mint"),
    ("FIIs turn net buyers; {sym} eyes fresh record high", "Economic Times"),
    ("Profit booking drags {sym} lower amid global cues", "Moneycontrol"),
    ("RBI policy in focus: {sym} rangebound ahead of decision", "Business Standard"),
    ("IT majors weigh on {sym} after weak guidance, shares slump", "Reuters"),
    ("{sym} options data hints at strong support build-up near spot", "NDTV Profit"),
    ("Crude oil cools, {sym} gains as inflation fears ease", "Bloomberg"),
    ("Auto and FMCG drag {sym}; analysts flag selloff risk", "CNBC-TV18"),
]


def llm(creds: Credentials):
    """Return a ChatGroq instance, or None when no key / library is available."""
    if not creds.has_groq:
        return None
    try:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=get_settings().groq_model,
            api_key=creds.groq_api_key,
            temperature=0.2,
            max_tokens=512,
        )
    except Exception:
        return None


def _keyword_sentiment(text: str) -> str:
    t = text.lower()
    pos = sum(w in t for w in _POSITIVE)
    neg = sum(w in t for w in _NEGATIVE)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def get_news(creds: Credentials, symbol: str) -> list[dict]:
    """Generate a small headline feed and tag each with Groq sentiment
    (falling back to keyword tagging)."""
    rnd = random.Random(f"news:{symbol}:{datetime.now(timezone.utc):%Y-%m-%d-%H}")
    chosen = rnd.sample(_HEADLINE_TEMPLATES, k=5)
    now = datetime.now(timezone.utc)

    items = []
    for i, (tmpl, src) in enumerate(chosen):
        title = tmpl.format(sym=symbol)
        items.append(
            {
                "title": title,
                "source": src,
                "publishedAt": (now - timedelta(minutes=18 * (i + 1))).isoformat(),
                "sentiment": _keyword_sentiment(title),
                "summary": None,
            }
        )

    model = llm(creds)
    if model is not None:
        try:
            joined = "\n".join(f"{i+1}. {it['title']}" for i, it in enumerate(items))
            prompt = (
                "Classify each headline's market sentiment as exactly one of "
                "positive, negative, or neutral. Reply with only the numbered "
                f"labels, one per line.\n\n{joined}"
            )
            resp = model.invoke(prompt)
            lines = [l.strip().lower() for l in str(resp.content).splitlines() if l.strip()]
            for it, line in zip(items, lines):
                for label in ("positive", "negative", "neutral"):
                    if label in line:
                        it["sentiment"] = label
                        break
        except Exception:
            pass  # keep keyword tags

    return items

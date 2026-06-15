"""Groq access: an LLM factory for the agents and news-sentiment tagging.

Everything degrades gracefully: without a Groq key we keyword-tag sentiment
and the agents run on deterministic heuristics instead of the LLM.
"""
from __future__ import annotations

import os
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import httpx

from ..config import get_settings
from ..deps import Credentials

# Per-symbol Google News search terms for the live RSS feed.
_NEWS_QUERY = {
    "NIFTY": "Nifty 50 index",
    "BANKNIFTY": "Bank Nifty index",
    "FINNIFTY": "Nifty Financial Services index",
    "MIDCPNIFTY": "Nifty Midcap index",
    "SENSEX": "BSE Sensex",
}

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


def _fetch_rss_headlines(symbol: str, limit: int = 6) -> list[dict]:
    """Live headlines from Google News RSS (free, no key)."""
    query = quote_plus(f"{_NEWS_QUERY.get(symbol, symbol)} stock market")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    resp = httpx.get(url, timeout=6.0, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    items = []
    for item in list(root.iter("item"))[:limit]:
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        src_el = item.find("source")
        source = (src_el.text if src_el is not None else None) or "Google News"
        # Google News appends " - <source>" to titles; strip it.
        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)]
        pub = item.findtext("pubDate")
        try:
            published = parsedate_to_datetime(pub).isoformat()
        except (TypeError, ValueError):
            published = datetime.now(timezone.utc).isoformat()
        items.append(
            {"title": title, "source": source, "publishedAt": published,
             "sentiment": "neutral", "summary": None}
        )
    return items


def _template_headlines(symbol: str) -> list[dict]:
    rnd = random.Random(f"news:{symbol}:{datetime.now(timezone.utc):%Y-%m-%d-%H}")
    chosen = rnd.sample(_HEADLINE_TEMPLATES, k=5)
    now = datetime.now(timezone.utc)
    return [
        {
            "title": tmpl.format(sym=symbol),
            "source": src,
            "publishedAt": (now - timedelta(minutes=18 * (i + 1))).isoformat(),
            "sentiment": "neutral",
            "summary": None,
        }
        for i, (tmpl, src) in enumerate(chosen)
    ]


def get_news(creds: Credentials, symbol: str) -> list[dict]:
    """Live Google News headlines (fallback to templates), each tagged with
    Groq sentiment (fallback to keyword tagging)."""
    items = []
    if not os.environ.get("STOCKLENS_OFFLINE"):  # skip network in tests/CI
        try:
            items = _fetch_rss_headlines(symbol)
        except Exception:
            items = []
    if not items:
        items = _template_headlines(symbol)

    # Baseline keyword sentiment.
    for it in items:
        it["sentiment"] = _keyword_sentiment(it["title"])

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

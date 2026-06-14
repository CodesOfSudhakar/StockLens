"""LangGraph pipeline: three specialists fan out from START, then the
Supervisor converges their outputs into a final outlook.

    START ──┬─> technical ─┐
            ├─> oi ────────┼─> supervisor ─> END
            └─> news ──────┘
"""
from __future__ import annotations

from collections import Counter

from langgraph.graph import END, START, StateGraph

from ..deps import Credentials
from ..services import angel_one, groq_client, indicators, oi_analysis
from . import news_agent, oi_agent, supervisor, technical_agent
from .state import PipelineState


def _build_facts(creds: Credentials, symbol: str) -> dict:
    """Collect raw signals once, so each agent reasons over the same facts."""
    candles, rsi = angel_one.get_candles_and_rsi(creds, symbol, "1D")
    closes = [c["close"] for c in candles]
    oi = angel_one.get_oi(creds, symbol, closes[-1] if closes else 0.0)
    news_items = groq_client.get_news(creds, symbol)

    # --- technical facts ---
    tsig, treason = indicators.ema_stack_signal(closes)
    technical = {
        "signal": tsig,
        "reasoning": treason,
        "price": closes[-1] if closes else 0.0,
        "ema9": indicators.ema(closes, 9)[-1] if closes else 0.0,
        "ema26": indicators.ema(closes, 26)[-1] if closes else 0.0,
        "ema50": indicators.ema(closes, 50)[-1] if closes else 0.0,
        "ema100": indicators.ema(closes, 100)[-1] if closes else 0.0,
        "rsi": rsi[-1]["value"] if rsi else 50.0,
    }

    # --- OI facts ---
    osig, oreason = oi_analysis.pcr_signal(oi["pcr"])
    buildups = Counter(r["ceBuildup"] for r in oi["chain"]) + Counter(
        r["peBuildup"] for r in oi["chain"]
    )
    oi_facts = {
        "signal": osig,
        "reasoning": oreason
        + f" Max Pain {oi['maxPain']} vs spot {oi['spot']:.0f}.",
        "pcr": oi["pcr"],
        "maxPain": oi["maxPain"],
        "spot": oi["spot"],
        "step": oi["chain"][0]["step"] if oi["chain"] else 50,
        "buildups": dict(buildups),
    }

    # --- news facts ---
    score = sum(
        {"positive": 1, "negative": -1}.get(it["sentiment"], 0) for it in news_items
    )
    nsig = "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
    news_facts = {
        "signal": nsig,
        "reasoning": f"Net headline sentiment score {score:+d} across {len(news_items)} stories.",
        "items": news_items,
    }

    return {
        "symbol": symbol,
        "technical": technical,
        "oi": oi_facts,
        "news": news_facts,
    }


def build_graph(model):
    """Compile the StateGraph. `model` is a ChatGroq instance or None."""
    g = StateGraph(PipelineState)

    # Node names must not collide with state keys (technical/oi/news/final).
    g.add_node("technical_agent", lambda s: {"technical": technical_agent.analyze(s["facts"], model)})
    g.add_node("oi_agent", lambda s: {"oi": oi_agent.analyze(s["facts"], model)})
    g.add_node("news_agent", lambda s: {"news": news_agent.analyze(s["facts"], model)})
    g.add_node(
        "supervisor_agent",
        lambda s: {
            "final": supervisor.synthesize(
                s["facts"], s["technical"], s["oi"], s["news"], model
            )
        },
    )

    # fan out
    g.add_edge(START, "technical_agent")
    g.add_edge(START, "oi_agent")
    g.add_edge(START, "news_agent")
    # converge
    g.add_edge("technical_agent", "supervisor_agent")
    g.add_edge("oi_agent", "supervisor_agent")
    g.add_edge("news_agent", "supervisor_agent")
    g.add_edge("supervisor_agent", END)

    return g.compile()


def run_pipeline(creds: Credentials, symbol: str) -> dict:
    facts = _build_facts(creds, symbol)
    model = groq_client.llm(creds)
    graph = build_graph(model)

    out = graph.invoke({"symbol": symbol, "facts": facts})
    final = out["final"]

    return {
        "symbol": symbol,
        "bias": final["bias"],
        "range": final["range"],
        "keyLevels": final["keyLevels"],
        "risk": final["risk"],
        "confidence": final.get("confidence"),
        "summary": final["summary"],
        "agents": {
            "technical": out["technical"],
            "oi": out["oi"],
            "news": out["news"],
        },
        "source": "groq" if model is not None else "heuristic",
    }

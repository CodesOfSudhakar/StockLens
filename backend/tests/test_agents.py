from app.agents import graph, supervisor


def test_build_facts_structure(no_creds):
    facts = graph._build_facts(no_creds, "NIFTY")
    assert facts["symbol"] == "NIFTY"
    for key in ("technical", "oi", "news"):
        assert key in facts
        assert facts[key]["signal"] in {"bullish", "bearish", "neutral"}
    assert "buildups" in facts["oi"]
    assert facts["oi"]["spot"] > 0


def test_run_pipeline_heuristic_path(no_creds):
    out = graph.run_pipeline(no_creds, "BANKNIFTY")
    assert out["symbol"] == "BANKNIFTY"
    assert out["bias"] in {"Bullish", "Bearish", "Neutral"}
    assert set(out["agents"]) == {"technical", "oi", "news"}
    assert out["source"] == "heuristic"  # no Groq key
    assert 0 <= out["confidence"] <= 100
    assert out["range"] and out["keyLevels"] and out["risk"] and out["summary"]


def test_run_pipeline_all_indices(no_creds):
    for sym in ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"):
        out = graph.run_pipeline(no_creds, sym)
        assert out["bias"] in {"Bullish", "Bearish", "Neutral"}


def test_run_pipeline_deterministic(no_creds):
    a = graph.run_pipeline(no_creds, "NIFTY")
    b = graph.run_pipeline(no_creds, "NIFTY")
    assert a["bias"] == b["bias"]
    assert a["confidence"] == b["confidence"]


def test_supervisor_heuristic_bullish():
    facts = {"symbol": "X", "oi": {"spot": 100.0, "step": 50, "maxPain": 100, "pcr": 1.3}}
    tech = {"signal": "bullish", "reasoning": "up"}
    oi = {"signal": "bullish", "reasoning": "puts"}
    news = {"signal": "bullish", "reasoning": "good"}
    res = supervisor.synthesize(facts, tech, oi, news, model=None)
    assert res["bias"] == "Bullish"
    assert res["confidence"] > 50


def test_supervisor_heuristic_conflict_is_neutral():
    facts = {"symbol": "X", "oi": {"spot": 100.0, "step": 50, "maxPain": 100, "pcr": 1.0}}
    tech = {"signal": "bullish", "reasoning": "up"}
    oi = {"signal": "bearish", "reasoning": "calls"}
    news = {"signal": "neutral", "reasoning": "mixed"}
    res = supervisor.synthesize(facts, tech, oi, news, model=None)
    assert res["bias"] == "Neutral"

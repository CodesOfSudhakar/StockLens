import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------- health ----------
def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- overview ----------
def test_overview_ok():
    r = client.get("/api/market/overview")
    assert r.status_code == 200
    data = r.json()
    assert len(data["indices"]) == 5
    assert data["breadth"]["advances"] > 0


# ---------- analysis ----------
def test_analysis_defaults():
    r = client.get("/api/analysis")
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "NIFTY"
    assert data["timeframe"] == "1D"
    assert data["candles"] and data["rsi"]
    assert "pcr" in data["oi"] and data["oi"]["chain"]
    assert len(data["news"]) == 5


def test_analysis_includes_phase2_analytics():
    data = client.get("/api/analysis", params={"symbol": "NIFTY"}).json()
    # Fibonacci
    assert data["fibonacci"]["direction"] in {"up", "down"}
    assert data["fibonacci"]["levels"]
    # Greeks (ATM band of 5 strikes, ATM call delta near 0.5)
    g = data["greeks"]
    assert len(g["rows"]) == 5 and 0 < g["sigma"] < 1
    atm_row = next(r for r in g["rows"] if r["strike"] == g["atm"])
    assert 0.3 < atm_row["ce"]["delta"] < 0.7
    # Harmonics is a list (possibly empty)
    assert isinstance(data["harmonics"], list)


@pytest.mark.parametrize("tf", ["1H", "4H", "1D", "1W"])
def test_analysis_each_timeframe(tf):
    r = client.get("/api/analysis", params={"symbol": "BANKNIFTY", "timeframe": tf})
    assert r.status_code == 200
    assert r.json()["timeframe"] == tf


def test_analysis_symbol_lowercased_is_uppercased():
    r = client.get("/api/analysis", params={"symbol": "nifty"})
    assert r.status_code == 200
    assert r.json()["symbol"] == "NIFTY"


def test_analysis_unknown_symbol_still_200():
    # Negative: unknown symbol should fall back to mock generator, not 500.
    r = client.get("/api/analysis", params={"symbol": "FOOBAR"})
    assert r.status_code == 200
    assert r.json()["candles"]


def test_analysis_unknown_timeframe_still_200():
    r = client.get("/api/analysis", params={"symbol": "NIFTY", "timeframe": "ZZ"})
    assert r.status_code == 200
    assert len(r.json()["candles"]) == 180  # 1D fallback


def test_news_endpoint():
    r = client.get("/api/analysis/news", params={"symbol": "FINNIFTY"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 5
    assert all(n["sentiment"] in {"positive", "negative", "neutral"} for n in body)


# ---------- outlook ----------
def test_outlook_ok():
    r = client.post("/api/outlook/run", json={"symbol": "NIFTY"})
    assert r.status_code == 200
    data = r.json()
    assert data["bias"] in {"Bullish", "Bearish", "Neutral"}
    assert set(data["agents"]) == {"technical", "oi", "news"}


def test_outlook_empty_body_defaults_nifty():
    r = client.post("/api/outlook/run", json={})
    assert r.status_code == 200
    assert r.json()["symbol"] == "NIFTY"


def test_outlook_passes_credentials_header_without_error():
    # Supplying a (fake) Groq key still must not 500 — llm() returns None on failure.
    r = client.post(
        "/api/outlook/run",
        json={"symbol": "SENSEX"},
        headers={"X-Groq-Api-Key": "gsk_invalid_key_for_test"},
    )
    assert r.status_code == 200


# ---------- negative / regression ----------
def test_unknown_route_404():
    assert client.get("/api/does-not-exist").status_code == 404


def test_outlook_get_method_not_allowed():
    assert client.get("/api/outlook/run").status_code == 405


def test_outlook_bad_json_422():
    # symbol must be a string; a list should fail validation.
    r = client.post("/api/outlook/run", json={"symbol": ["NIFTY"]})
    assert r.status_code == 422

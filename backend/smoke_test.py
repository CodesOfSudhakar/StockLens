"""Quick end-to-end check with no credentials (exercises the mock paths
and the full LangGraph pipeline). Run: python smoke_test.py"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def check(name, resp, *keys):
    assert resp.status_code == 200, f"{name}: HTTP {resp.status_code} {resp.text}"
    data = resp.json()
    for k in keys:
        assert k in data, f"{name}: missing key '{k}'"
    print(f"  OK  {name}")
    return data


print("StockLens smoke test")

check("health", client.get("/api/health"), "status")

ov = check("market/overview", client.get("/api/market/overview"),
           "indices", "vix", "breadth", "gainers", "losers", "sentiment")
assert len(ov["indices"]) == 5, "expected 5 indices"

an = check("analysis", client.get("/api/analysis?symbol=NIFTY&timeframe=1D"),
          "candles", "rsi", "oi", "news")
assert an["candles"], "no candles"
assert "pcr" in an["oi"] and "maxPain" in an["oi"], "oi missing pcr/maxPain"
assert an["oi"]["chain"], "empty option chain"

out = check("outlook/run", client.post("/api/outlook/run", json={"symbol": "BANKNIFTY"}),
            "bias", "range", "keyLevels", "risk", "summary", "agents")
assert set(out["agents"]) == {"technical", "oi", "news"}, "missing agent outputs"

print(f"\nAll checks passed.")
print(f"  sample bias : {out['bias']} (confidence {out.get('confidence')})")
print(f"  pipeline    : {out['source']}")
print(f"  data source : {an['source']}")

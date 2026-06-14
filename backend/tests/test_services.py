import pytest

from app.deps import Credentials, get_credentials
from app.services import angel_one, groq_client


# ---------- Credentials ----------
def test_credentials_has_angel_requires_all_three():
    c = Credentials("id", "key", "", "", "")
    assert not c.has_angel
    c2 = Credentials("id", "key", "pin", "", "")
    assert c2.has_angel


def test_credentials_has_groq():
    assert not Credentials("", "", "", "", "").has_groq
    assert Credentials("", "", "", "", "gsk_x").has_groq


def test_get_credentials_falls_back_to_env(monkeypatch):
    # No headers -> uses settings defaults (empty by default here).
    creds = get_credentials()
    assert isinstance(creds, Credentials)


def test_get_credentials_headers_take_priority():
    creds = get_credentials(
        x_angel_client_id="ABC",
        x_angel_api_key="K",
        x_angel_pin="1234",
        x_groq_api_key="gsk_test",
    )
    assert creds.angel_client_id == "ABC"
    assert creds.has_angel and creds.has_groq


# ---------- angel_one ----------
def test_live_session_none_without_creds(no_creds):
    assert angel_one._live_session(no_creds) is None


def test_overview_shape(no_creds):
    ov = angel_one.get_overview(no_creds)
    assert len(ov["indices"]) == 5
    assert {"advances", "declines"} <= ov["breadth"].keys()
    assert ov["sentiment"] in {"bullish", "bearish", "neutral"}
    assert len(ov["gainers"]) == 4 and len(ov["losers"]) == 4
    assert ov["source"] == "mock"


def test_overview_gainers_sorted_desc(no_creds):
    ov = angel_one.get_overview(no_creds)
    pcts = [g["changePct"] for g in ov["gainers"]]
    assert pcts == sorted(pcts, reverse=True)


@pytest.mark.parametrize("tf,expected", [("1H", 168), ("4H", 120), ("1D", 180), ("1W", 120)])
def test_candle_counts_per_timeframe(no_creds, tf, expected):
    candles, rsi = angel_one.get_candles_and_rsi(no_creds, "NIFTY", tf)
    assert len(candles) == expected
    assert len(rsi) == expected


def test_candles_deterministic(no_creds):
    a, _ = angel_one.get_candles_and_rsi(no_creds, "NIFTY", "1D")
    b, _ = angel_one.get_candles_and_rsi(no_creds, "NIFTY", "1D")
    assert a == b  # same seed -> identical


def test_candles_ohlc_consistency(no_creds):
    candles, _ = angel_one.get_candles_and_rsi(no_creds, "BANKNIFTY", "1D")
    for c in candles:
        assert c["high"] >= c["open"] and c["high"] >= c["close"]
        assert c["low"] <= c["open"] and c["low"] <= c["close"]


def test_unknown_symbol_falls_back_to_nifty_meta(no_creds):
    # Should not raise; uses NIFTY anchor under the hood.
    candles, _ = angel_one.get_candles_and_rsi(no_creds, "DOESNOTEXIST", "1D")
    assert candles


def test_unknown_timeframe_falls_back_to_1d(no_creds):
    candles, _ = angel_one.get_candles_and_rsi(no_creds, "NIFTY", "BOGUS")
    assert len(candles) == 180  # the 1D default


def test_oi_structure(no_creds):
    candles, _ = angel_one.get_candles_and_rsi(no_creds, "NIFTY", "1D")
    spot = candles[-1]["close"]
    oi = angel_one.get_oi(no_creds, "NIFTY", spot)
    assert oi["chain"] and len(oi["chain"]) == 9
    assert oi["pcr"] >= 0
    assert isinstance(oi["maxPain"], int)
    for row in oi["chain"]:
        assert row["ceBuildup"] in {
            "Long Buildup", "Short Covering", "Long Unwinding", "Short Buildup"
        }


# ---------- groq_client ----------
def test_keyword_sentiment():
    assert groq_client._keyword_sentiment("Nifty surge and rally, strong gains") == "positive"
    assert groq_client._keyword_sentiment("Market crash, slumps on fears") == "negative"
    assert groq_client._keyword_sentiment("Market opens for trading") == "neutral"


def test_llm_none_without_key(no_creds):
    assert groq_client.llm(no_creds) is None


def test_get_news_without_key(no_creds):
    items = groq_client.get_news(no_creds, "NIFTY")
    assert len(items) == 5
    for n in items:
        assert n["sentiment"] in {"positive", "negative", "neutral"}
        assert n["title"] and n["source"] and n["publishedAt"]

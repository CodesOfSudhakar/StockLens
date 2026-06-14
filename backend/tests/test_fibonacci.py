import pytest

from app.services import fibonacci


def _c(close, high=None, low=None):
    return {"time": 0, "open": close, "high": high or close, "low": low or close, "close": close}


def test_none_when_too_few_candles():
    assert fibonacci.levels([_c(100), _c(101)]) is None


def test_none_when_flat():
    assert fibonacci.levels([_c(100) for _ in range(10)]) is None


def test_up_swing_levels():
    # low early, high late -> up swing
    candles = [_c(100, low=100)] + [_c(120 + i, high=120 + i) for i in range(10)]
    fib = fibonacci.levels(candles, lookback=50)
    assert fib is not None
    assert fib["direction"] == "up"
    assert fib["low"] == 100
    high, low = fib["high"], fib["low"]
    diff = high - low
    fifty = next(l for l in fib["levels"] if l["ratio"] == 0.5)
    assert fifty["price"] == pytest.approx(high - diff * 0.5, abs=0.01)


def test_levels_include_retracements_and_extensions():
    candles = [_c(100, low=100)] + [_c(110 + i, high=110 + i) for i in range(20)]
    fib = fibonacci.levels(candles)
    kinds = {l["kind"] for l in fib["levels"]}
    assert {"anchor", "retracement", "extension"} == kinds
    retr = [l["ratio"] for l in fib["levels"] if l["kind"] == "retracement"]
    assert 0.618 in retr

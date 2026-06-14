import math

import pytest

from app.services import indicators


# ---------- ema ----------
def test_ema_empty_returns_empty():
    assert indicators.ema([], 9) == []


def test_ema_single_value():
    assert indicators.ema([100.0], 9) == [100.0]


def test_ema_constant_series_converges_to_value():
    out = indicators.ema([50.0] * 30, 9)
    assert len(out) == 30
    assert all(abs(v - 50.0) < 1e-9 for v in out)


def test_ema_responds_to_trend():
    rising = list(range(1, 51))
    out = indicators.ema([float(x) for x in rising], 9)
    # EMA lags price, so last EMA should trail the last close but exceed the first.
    assert out[-1] < rising[-1]
    assert out[-1] > rising[0]


# ---------- rsi ----------
def test_rsi_short_series_defaults_to_50():
    assert indicators.rsi([1, 2, 3], 14) == [50.0, 50.0, 50.0]


def test_rsi_length_matches_input():
    closes = [float(x) for x in range(1, 60)]
    assert len(indicators.rsi(closes, 14)) == len(closes)


def test_rsi_all_gains_is_high():
    closes = [float(x) for x in range(1, 40)]  # strictly increasing
    out = indicators.rsi(closes, 14)
    assert out[-1] > 99  # no losses -> RSI saturates near 100


def test_rsi_all_losses_is_low():
    closes = [float(x) for x in range(40, 0, -1)]  # strictly decreasing
    out = indicators.rsi(closes, 14)
    assert out[-1] < 1  # no gains -> RSI near 0


def test_rsi_bounded_0_100():
    import random

    rnd = random.Random(7)
    closes = [100.0]
    for _ in range(200):
        closes.append(max(1.0, closes[-1] + rnd.uniform(-3, 3)))
    out = indicators.rsi(closes, 14)
    assert all(0 <= v <= 100 for v in out)


# ---------- ema_stack_signal ----------
def test_stack_signal_insufficient_history():
    sig, reason = indicators.ema_stack_signal([1.0, 2.0, 3.0])
    assert sig == "neutral"
    assert "Insufficient" in reason


def test_stack_signal_bullish_on_uptrend():
    closes = [float(x) for x in range(1, 200)]
    sig, _ = indicators.ema_stack_signal(closes)
    assert sig == "bullish"


def test_stack_signal_bearish_on_downtrend():
    closes = [float(x) for x in range(200, 1, -1)]
    sig, _ = indicators.ema_stack_signal(closes)
    assert sig == "bearish"


def test_stack_signal_neutral_on_flat():
    closes = [100.0] * 150
    sig, _ = indicators.ema_stack_signal(closes)
    assert sig == "neutral"

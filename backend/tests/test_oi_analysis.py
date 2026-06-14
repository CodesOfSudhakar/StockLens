import pytest

from app.services import oi_analysis


# ---------- classify_buildup (4 quadrants + boundaries) ----------
@pytest.mark.parametrize(
    "oi_change, price_change, expected",
    [
        (100, 5.0, "Long Buildup"),
        (100, -5.0, "Short Buildup"),
        (-100, 5.0, "Short Covering"),
        (-100, -5.0, "Long Unwinding"),
        # boundary: zeros count as the non-negative branch
        (0, 0.0, "Long Buildup"),
        (0, -1.0, "Short Buildup"),
        (-1, 0.0, "Short Covering"),
    ],
)
def test_classify_buildup(oi_change, price_change, expected):
    assert oi_analysis.classify_buildup(oi_change, price_change) == expected


def test_classify_buildup_returns_only_valid_labels():
    valid = {"Long Buildup", "Short Covering", "Long Unwinding", "Short Buildup"}
    for o in (-1, 0, 1):
        for p in (-1.0, 0.0, 1.0):
            assert oi_analysis.classify_buildup(o, p) in valid


# ---------- pcr ----------
def test_pcr_basic():
    chain = [{"ceOi": 100, "peOi": 200}, {"ceOi": 100, "peOi": 100}]
    assert oi_analysis.pcr(chain) == 1.5


def test_pcr_zero_calls_does_not_divide_by_zero():
    chain = [{"ceOi": 0, "peOi": 500}]
    assert oi_analysis.pcr(chain) == 0.0


def test_pcr_empty_chain():
    assert oi_analysis.pcr([]) == 0.0


# ---------- max_pain ----------
def test_max_pain_single_strike():
    chain = [{"strike": 100, "ceOi": 10, "peOi": 10}]
    assert oi_analysis.max_pain(chain) == 100


def test_max_pain_is_a_listed_strike():
    chain = [
        {"strike": 100, "ceOi": 50, "peOi": 10},
        {"strike": 110, "ceOi": 30, "peOi": 30},
        {"strike": 120, "ceOi": 10, "peOi": 50},
    ]
    mp = oi_analysis.max_pain(chain)
    assert mp in {100, 110, 120}


def test_max_pain_symmetric_chain_centers():
    # Symmetric OI around 110 -> max pain should land at the centre strike.
    chain = [
        {"strike": 100, "ceOi": 10, "peOi": 30},
        {"strike": 110, "ceOi": 20, "peOi": 20},
        {"strike": 120, "ceOi": 30, "peOi": 10},
    ]
    assert oi_analysis.max_pain(chain) == 110


# ---------- pcr_signal ----------
@pytest.mark.parametrize(
    "value, expected",
    [(1.5, "bullish"), (1.2, "bullish"), (0.8, "bearish"), (0.5, "bearish"), (1.0, "neutral")],
)
def test_pcr_signal_thresholds(value, expected):
    sig, _ = oi_analysis.pcr_signal(value)
    assert sig == expected

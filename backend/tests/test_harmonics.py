from app.services import harmonics


def _candles(closes):
    return [{"time": i, "open": c, "high": c, "low": c, "close": c} for i, c in enumerate(closes)]


def test_zigzag_picks_alternating_pivots():
    closes = [100, 110, 100, 110, 100]  # clear 10% swings
    pivots = harmonics.zigzag(_candles(closes), pct=0.03)
    types = [p["type"] for p in pivots]
    # alternating H/L
    assert all(types[i] != types[i + 1] for i in range(len(types) - 1))
    assert len(pivots) >= 4


def test_zigzag_ignores_noise_below_threshold():
    closes = [100, 100.5, 100.2, 100.6]  # all < 3% moves
    pivots = harmonics.zigzag(_candles(closes), pct=0.03)
    assert len(pivots) <= 2


def test_detects_gartley():
    # X1000 -> A1100 -> B1038.2 -> C1075 -> D1021.4 (Gartley ratios)
    closes = [1000, 1100, 1038.2, 1075, 1021.4]
    found = harmonics.detect(_candles(closes), pct=0.02)
    names = [p["name"] for p in found]
    assert "Gartley" in names
    g = next(p for p in found if p["name"] == "Gartley")
    assert g["direction"] == "bullish"  # completes at a low
    assert g["prz"] == 1021.4


def test_no_pattern_on_monotonic_trend():
    closes = [100 + i for i in range(30)]  # straight line, < 5 pivots
    assert harmonics.detect(_candles(closes)) == []

from app.services import live_transforms, scrip_master


# ---------- candles_from_angel ----------
def test_candles_from_angel_parses_and_sorts():
    rows = [
        ["2024-01-25T11:15:00+05:30", 100, 105, 99, 104, 1000],
        ["2024-01-25T09:15:00+05:30", 95, 101, 94, 100, 800],
    ]
    candles = live_transforms.candles_from_angel(rows)
    assert len(candles) == 2
    assert candles[0]["time"] < candles[1]["time"]  # sorted ascending
    assert candles[0]["open"] == 95.0


def test_candles_from_angel_skips_malformed():
    rows = [["bad-ts", 1, 2, 3, 4], ["2024-01-25T09:15:00+05:30", 1, 2, 0.5, 1.5]]
    assert len(live_transforms.candles_from_angel(rows)) == 1


# ---------- resample ----------
def _c(t, o, h, l, cl):
    return {"time": t, "open": o, "high": h, "low": l, "close": cl}


def test_resample_passthrough():
    data = [_c(0, 1, 2, 0, 1)]
    assert live_transforms.resample(data, None) == data


def test_resample_x4_aggregates_four():
    data = [_c(i, 10 + i, 20 + i, 5 + i, 12 + i) for i in range(8)]
    out = live_transforms.resample(data, "x4")
    assert len(out) == 2
    assert out[0]["open"] == data[0]["open"]
    assert out[0]["close"] == data[3]["close"]
    assert out[0]["high"] == max(c["high"] for c in data[:4])
    assert out[0]["low"] == min(c["low"] for c in data[:4])


def test_resample_weekly_groups_by_week():
    # two timestamps in different ISO weeks
    wk1 = 1706140800  # 2024-01-25
    wk2 = wk1 + 7 * 86400
    data = [_c(wk1, 1, 2, 0, 1), _c(wk1 + 3600, 1, 3, 0, 2), _c(wk2, 5, 6, 4, 5)]
    out = live_transforms.resample(data, "weekly")
    assert len(out) == 2


# ---------- quotes / chain ----------
def test_movers_and_breadth():
    changes = {"A": 5.0, "B": 2.0, "C": -1.0, "D": -3.0, "E": 0.0, "F": 4.0, "G": -2.0}
    out = live_transforms.movers_and_breadth(changes)
    assert out["gainers"][0]["symbol"] == "A"  # highest first
    assert out["losers"][0]["symbol"] == "D"  # most negative first
    assert out["breadth"]["advances"] == 3  # A,B,F
    assert out["breadth"]["declines"] == 3  # C,D,G
    assert out["breadth"]["unchanged"] == 1  # E


def test_equity_tokens_resolution():
    rows = [
        {"symbol": "RELIANCE-EQ", "exch_seg": "NSE", "token": "2885"},
        {"symbol": "TCS-EQ", "exch_seg": "NSE", "token": "11536"},
        {"symbol": "RELIANCE", "exch_seg": "BSE", "token": "500325"},  # wrong seg
        {"symbol": "INFY-EQ", "exch_seg": "NSE", "token": "1594"},
    ]
    out = scrip_master.equity_tokens(["RELIANCE", "TCS", "NOTLISTED"], rows)
    assert out == {"RELIANCE": "2885", "TCS": "11536"}


def test_parse_index_quote():
    q = live_transforms.parse_index_quote(
        "NIFTY", "Nifty 50", {"ltp": 24800.5, "netChange": 50.2, "percentChange": 0.2}
    )
    assert q["symbol"] == "NIFTY" and q["ltp"] == 24800.5 and q["change"] == 50.2


def test_build_option_chain():
    spot, step = 20000, 50
    instruments = []
    quotes = {}
    for k in range(-2, 3):
        strike = 20000 + k * step
        for typ, tok in (("CE", f"c{k}"), ("PE", f"p{k}")):
            instruments.append({"strike": strike, "type": typ, "token": tok, "exchange": "NFO"})
            quotes[tok] = {"opnInterest": 1000 + abs(k), "netChange": -5 if typ == "CE" else 5}
    chain = live_transforms.build_option_chain(instruments, quotes, spot, step)
    assert chain["spot"] == 20000
    assert len(chain["chain"]) == 5
    assert chain["pcr"] > 0
    row = chain["chain"][0]
    assert row["ceOi"] > 0 and row["peOi"] > 0
    assert row["ceBuildup"] in {"Long Buildup", "Short Covering", "Long Unwinding", "Short Buildup"}


# ---------- scrip master parsing ----------
def test_option_chain_instruments_picks_nearest_expiry():
    rows = [
        {"name": "NIFTY", "instrumenttype": "OPTIDX", "symbol": "NIFTY25JAN2030000CE",
         "expiry": "25JAN2030", "strike": "2000000", "token": "1", "exch_seg": "NFO"},
        {"name": "NIFTY", "instrumenttype": "OPTIDX", "symbol": "NIFTY25JAN2030000PE",
         "expiry": "25JAN2030", "strike": "2000000", "token": "2", "exch_seg": "NFO"},
        {"name": "NIFTY", "instrumenttype": "OPTIDX", "symbol": "NIFTY25DEC2035000CE",
         "expiry": "25DEC2035", "strike": "2050000", "token": "3", "exch_seg": "NFO"},
    ]
    expiry, instruments = scrip_master.option_chain_instruments("NIFTY", rows)
    assert expiry is not None
    # nearest expiry is 25JAN2030 -> two instruments, strike scaled /100
    assert len(instruments) == 2
    assert instruments[0]["strike"] == 20000
    assert {i["type"] for i in instruments} == {"CE", "PE"}


def test_option_chain_instruments_empty_master():
    expiry, instruments = scrip_master.option_chain_instruments("NIFTY", [])
    assert expiry is None and instruments == []

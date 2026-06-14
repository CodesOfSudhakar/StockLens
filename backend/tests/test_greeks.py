import math

import pytest

from app.services import greeks


# Reference: S=K=100, T=1, r=0, sigma=0.2 -> BS call ~ 7.9656, delta ~ 0.5398
def test_atm_call_price_reference():
    assert greeks.price(100, 100, 1.0, 0.0, 0.2, "CE") == pytest.approx(7.97, abs=0.05)


def test_put_call_parity():
    S, K, T, r, sig = 100, 95, 0.5, 0.06, 0.25
    c = greeks.price(S, K, T, r, sig, "CE")
    p = greeks.price(S, K, T, r, sig, "PE")
    # C - P = S - K e^{-rT}
    assert (c - p) == pytest.approx(S - K * math.exp(-r * T), abs=0.05)


def test_call_delta_between_0_and_1():
    g = greeks.greeks(100, 100, 1.0, 0.0, 0.2, "CE")
    assert 0 < g["delta"] < 1
    assert g["delta"] == pytest.approx(0.54, abs=0.02)


def test_put_delta_negative():
    g = greeks.greeks(100, 100, 1.0, 0.0, 0.2, "PE")
    assert -1 < g["delta"] < 0


def test_call_put_delta_differ_by_one():
    c = greeks.greeks(100, 100, 1.0, 0.0, 0.2, "CE")["delta"]
    p = greeks.greeks(100, 100, 1.0, 0.0, 0.2, "PE")["delta"]
    assert (c - p) == pytest.approx(1.0, abs=0.01)


def test_gamma_vega_positive():
    g = greeks.greeks(100, 100, 0.5, 0.06, 0.2, "CE")
    assert g["gamma"] > 0
    assert g["vega"] > 0


def test_expired_option_is_intrinsic():
    assert greeks.price(110, 100, 0, 0.06, 0.2, "CE") == 10.0
    assert greeks.price(90, 100, 0, 0.06, 0.2, "PE") == 10.0
    assert greeks.greeks(110, 100, 0, 0.06, 0.2, "CE")["gamma"] == 0.0


def test_implied_vol_recovers_sigma():
    true_sigma = 0.22
    mkt = greeks.price(100, 105, 0.4, 0.06, true_sigma, "CE")
    iv = greeks.implied_vol(mkt, 100, 105, 0.4, 0.06, "CE")
    assert iv == pytest.approx(true_sigma, abs=0.01)


def test_chain_greeks_shape():
    rows = greeks.chain_greeks(20000, [19900, 20000, 20100], 0.15, 7)
    assert len(rows) == 3
    assert {"strike", "ce", "pe"} <= rows[0].keys()
    assert {"delta", "gamma", "theta", "vega", "rho"} <= rows[0]["ce"].keys()

"""Black-Scholes option pricing and Greeks (European, no dividend).

Used to surface delta/gamma/theta/vega and implied volatility for index
options. Pure math — fully unit-testable against known values.
"""
from __future__ import annotations

import math

SQRT_2PI = math.sqrt(2 * math.pi)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def _d1_d2(S, K, T, r, sigma):
    vol = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / vol
    return d1, d1 - vol


def price(S, K, T, r, sigma, kind="CE") -> float:
    """Black-Scholes price. CE = call, PE = put."""
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0.0) if kind == "CE" else max(K - S, 0.0)
        return round(intrinsic, 2)
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    if kind == "CE":
        val = S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    else:
        val = K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)
    return round(val, 2)


def greeks(S, K, T, r, sigma, kind="CE") -> dict:
    """Return delta, gamma, theta (per day), vega (per 1% vol), rho."""
    if T <= 0 or sigma <= 0:
        intrinsic_delta = (1.0 if S > K else 0.0) if kind == "CE" else (-1.0 if S < K else 0.0)
        return {"delta": intrinsic_delta, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

    d1, d2 = _d1_d2(S, K, T, r, sigma)
    pdf = _norm_pdf(d1)
    sqrtT = math.sqrt(T)
    disc = math.exp(-r * T)

    gamma = pdf / (S * sigma * sqrtT)
    vega = S * pdf * sqrtT / 100  # per 1 percentage-point change in vol

    if kind == "CE":
        delta = _norm_cdf(d1)
        theta = (-(S * pdf * sigma) / (2 * sqrtT) - r * K * disc * _norm_cdf(d2)) / 365
        rho = K * T * disc * _norm_cdf(d2) / 100
    else:
        delta = _norm_cdf(d1) - 1
        theta = (-(S * pdf * sigma) / (2 * sqrtT) + r * K * disc * _norm_cdf(-d2)) / 365
        rho = -K * T * disc * _norm_cdf(-d2) / 100

    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 2),
        "vega": round(vega, 2),
        "rho": round(rho, 2),
    }


def implied_vol(market_price, S, K, T, r, kind="CE", tol=1e-4, max_iter=100):
    """Solve for implied volatility via Newton-Raphson (bisection fallback)."""
    if T <= 0 or market_price <= 0:
        return None
    sigma = 0.25
    for _ in range(max_iter):
        p = price(S, K, T, r, sigma, kind)
        g = greeks(S, K, T, r, sigma, kind)
        vega = g["vega"] * 100  # back to per-unit
        diff = p - market_price
        if abs(diff) < tol:
            return round(sigma, 4)
        if vega < 1e-8:
            break
        sigma = max(1e-4, sigma - diff / vega)
    # Bisection fallback
    lo, hi = 1e-4, 5.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if price(S, K, T, r, mid, kind) > market_price:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2, 4)


def chain_greeks(spot, strikes, sigma, t_days, r=0.065) -> list[dict]:
    """Greeks for a band of strikes (CE + PE each) at an assumed volatility."""
    T = max(t_days, 0.5) / 365
    out = []
    for k in strikes:
        out.append(
            {
                "strike": k,
                "ce": greeks(spot, k, T, r, sigma, "CE"),
                "pe": greeks(spot, k, T, r, sigma, "PE"),
            }
        )
    return out

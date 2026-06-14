import math
import statistics
from datetime import date

from fastapi import APIRouter, Depends, Query

from ..schemas import Analysis, NewsItem
from ..deps import Credentials, get_credentials
from ..services import angel_one, fibonacci, greeks, groq_client, harmonics

router = APIRouter(prefix="/analysis", tags=["analysis"])

RISK_FREE = 0.065  # ~India 1y T-bill


def _realized_vol(candles: list[dict]) -> float:
    """Annualised realised volatility from close-to-close log returns."""
    closes = [c["close"] for c in candles]
    rets = [
        math.log(closes[i] / closes[i - 1])
        for i in range(1, len(closes))
        if closes[i - 1] > 0
    ]
    if len(rets) < 2:
        return 0.15
    vol = statistics.pstdev(rets) * math.sqrt(252)
    return round(max(0.08, min(0.6, vol)), 4)


def _days_to_weekly_expiry() -> int:
    """Days until the next Thursday (NSE weekly index expiry)."""
    dow = date.today().weekday()  # Mon=0 … Thu=3
    return (3 - dow) % 7 or 1


@router.get("", response_model=Analysis)
def analysis(
    symbol: str = Query("NIFTY"),
    timeframe: str = Query("1D"),
    creds: Credentials = Depends(get_credentials),
) -> Analysis:
    symbol = symbol.upper()
    candles, rsi = angel_one.get_candles_and_rsi(creds, symbol, timeframe)
    spot = candles[-1]["close"] if candles else 0.0
    oi = angel_one.get_oi(creds, symbol, spot)
    news = groq_client.get_news(creds, symbol)

    # --- Phase 2 analytics ---
    fib = fibonacci.levels(candles)

    step = oi["chain"][0]["step"] if oi["chain"] else 50
    atm = round(spot / step) * step
    sigma = _realized_vol(candles)
    t_days = _days_to_weekly_expiry()
    strike_band = [atm + k * step for k in range(-2, 3)]
    greeks_data = {
        "sigma": sigma,
        "tDays": float(t_days),
        "r": RISK_FREE,
        "atm": int(atm),
        "rows": greeks.chain_greeks(spot, strike_band, sigma, t_days, RISK_FREE),
    }

    patterns = harmonics.detect(candles)

    source = "live" if creds.has_angel else "mock"
    return Analysis(
        symbol=symbol,
        timeframe=timeframe,
        candles=candles,
        rsi=rsi,
        oi=oi,
        news=news,
        fibonacci=fib,
        greeks=greeks_data,
        harmonics=patterns,
        source=source,
    )


@router.get("/news", response_model=list[NewsItem])
def news(
    symbol: str = Query("NIFTY"),
    creds: Credentials = Depends(get_credentials),
) -> list[NewsItem]:
    return [NewsItem(**n) for n in groq_client.get_news(creds, symbol.upper())]

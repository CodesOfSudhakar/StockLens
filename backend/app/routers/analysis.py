from fastapi import APIRouter, Depends, Query

from ..deps import Credentials, get_credentials
from ..schemas import Analysis, NewsItem
from ..services import angel_one, groq_client

router = APIRouter(prefix="/analysis", tags=["analysis"])


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

    source = "live" if creds.has_angel else "mock"
    return Analysis(
        symbol=symbol,
        timeframe=timeframe,
        candles=candles,
        rsi=rsi,
        oi=oi,
        news=news,
        source=source,
    )


@router.get("/news", response_model=list[NewsItem])
def news(
    symbol: str = Query("NIFTY"),
    creds: Credentials = Depends(get_credentials),
) -> list[NewsItem]:
    return [NewsItem(**n) for n in groq_client.get_news(creds, symbol.upper())]

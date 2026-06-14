from pydantic import BaseModel, Field


# ---- Market overview ----
class IndexQuote(BaseModel):
    symbol: str
    label: str
    ltp: float
    change: float
    changePct: float


class Breadth(BaseModel):
    advances: int
    declines: int
    unchanged: int = 0


class Mover(BaseModel):
    symbol: str
    changePct: float


class Overview(BaseModel):
    indices: list[IndexQuote]
    vix: float
    breadth: Breadth
    gainers: list[Mover]
    losers: list[Mover]
    sentiment: str
    sentimentLabel: str
    source: str = "mock"


# ---- Analysis ----
class Candle(BaseModel):
    time: int  # unix seconds (lightweight-charts UTCTimestamp)
    open: float
    high: float
    low: float
    close: float


class RsiPoint(BaseModel):
    time: int
    value: float


class OIRow(BaseModel):
    strike: int
    step: int = 50
    ceOi: int
    peOi: int
    ceBuildup: str
    peBuildup: str


class OIData(BaseModel):
    spot: float
    pcr: float
    maxPain: int
    chain: list[OIRow]


class NewsItem(BaseModel):
    title: str
    source: str
    publishedAt: str
    sentiment: str
    summary: str | None = None


class Analysis(BaseModel):
    symbol: str
    timeframe: str
    candles: list[Candle]
    rsi: list[RsiPoint]
    oi: OIData
    news: list[NewsItem]
    source: str = "mock"


# ---- Outlook ----
class OutlookRequest(BaseModel):
    symbol: str = Field(default="NIFTY")


class AgentOutput(BaseModel):
    signal: str
    reasoning: str


class Outlook(BaseModel):
    symbol: str
    bias: str
    range: str
    keyLevels: str
    risk: str
    confidence: int | None = None
    summary: str
    agents: dict[str, AgentOutput]
    source: str = "mock"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import analysis, market, outlook

settings = get_settings()

app = FastAPI(
    title="StockLens API",
    version="1.0.0",
    description="Indian market data, OI analytics, and a LangGraph outlook pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers are mounted under /api to match the Vite proxy.
app.include_router(market.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(outlook.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "stocklens"}

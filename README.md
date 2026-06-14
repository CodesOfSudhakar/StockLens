# StockLens 📈

A mobile-first **React PWA** for Indian stock-market analysis, backed by a
**FastAPI + LangGraph** service. Four screens, a three-agent AI outlook
pipeline, and graceful mock data so it runs out of the box — no credentials
required to demo.

> For research / education only. **Not investment advice.**

---

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | React + Vite + Tailwind + Framer Motion + TradingView Lightweight Charts |
| Backend  | FastAPI + LangChain + LangGraph + Groq (`llama3-70b`) + Angel One SmartAPI |
| PWA      | `vite-plugin-pwa` (manifest + service worker, offline cache) |

## Screens

1. **Home** — live indices (Nifty 50, Bank Nifty, Fin Nifty, MidCap, Sensex),
   India VIX, market breadth, top gainers/losers, overall sentiment pill.
2. **Analysis** — candlestick chart with EMA 9/26/50/100, timeframe toggle
   (1H/4H/1D/1W), RSI panel, option-chain OI table with buildup classification
   (Long Buildup / Short Covering / Long Unwinding / Short Buildup), PCR,
   Max Pain, and a Groq-tagged news feed.
3. **AI Outlook** — one button runs a LangGraph pipeline of three specialists
   (Technical · OI · News) converging on a Supervisor that outputs
   **Bias / Range / Key Levels / Risk** with a confidence score.
4. **Settings** — appearance (Light / Dark / System theme toggle), Angel One
   credentials, Groq API key, default index — all kept in `localStorage` and
   forwarded to the backend per request.

### Dark mode

A Light / Dark / System toggle lives under **Settings → Appearance**. Theme
applies instantly (no save needed) and persists. Neutrals are driven by CSS
variables (`--bg`, `--ink`, `--surface`, …) that flip on the `.dark` class, so
every surface — including the TradingView charts — recolours automatically.
`System` follows the OS preference live via `prefers-color-scheme`.

---

## Quick start

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # optional: fill in fallback creds
uvicorn app.main:app --reload --port 8000
```

API docs at <http://localhost:8000/docs>. Health check: `GET /api/health`.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> (the dev server proxies `/api` → `:8000`).
Best viewed at Pixel 7a width (≈412 px) — use device toolbar in DevTools.

### 3. Production build

```powershell
cd frontend
npm run build      # emits dist/ with the PWA service worker
npm run preview
```

---

## How credentials flow

The app never stores secrets server-side. Settings entered on the **Settings**
screen are saved to `localStorage` and sent on every request as `X-Angel-*` /
`X-Groq-Api-Key` headers (see [`store/settings.js`](frontend/src/store/settings.js)
and [`deps.py`](backend/app/deps.py)).

- **No Angel One creds** → deterministic synthetic market data.
- **No Groq key** → news sentiment is keyword-tagged and the agents run on
  heuristics instead of the LLM.

This means every feature is demoable immediately; adding real keys upgrades the
data and reasoning in place.

---

## Backend layout

```
backend/app/
├── main.py            # FastAPI app + CORS, mounts /api routers
├── config.py          # env settings
├── deps.py            # per-request Credentials from headers
├── schemas.py         # Pydantic response models
├── routers/           # market · analysis · outlook
├── services/          # angel_one · groq_client · indicators · oi_analysis
└── agents/            # LangGraph pipeline
    ├── graph.py       # START ─> [technical, oi, news] ─> supervisor ─> END
    ├── technical_agent.py · oi_agent.py · news_agent.py · supervisor.py
    └── state.py
```

## Testing

```powershell
# Backend — 74 tests (pytest)
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest

# Frontend — 19 tests (vitest + jsdom)
cd frontend
npm test
```

Coverage spans unit, edge-case, negative, and regression scenarios:

- **Indicators** — EMA/RSI on empty, single, constant, all-up, all-down and
  random series; RSI bounded 0–100; EMA-stack trend classification.
- **OI analytics** — all four buildup quadrants + boundaries, PCR with
  zero/empty chains (no divide-by-zero), Max Pain centring.
- **Data provider** — deterministic candles, OHLC consistency, correct counts
  per timeframe, unknown-symbol / unknown-timeframe fallbacks, live-session
  returns `None` without creds.
- **Agents** — `build_facts`, full pipeline across all five indices,
  determinism, supervisor synthesis (agreement vs. conflict).
- **API** — every endpoint, param defaults, unknown route (404), wrong method
  (405), invalid body (422), and a fake-Groq-key path that must not 500.
- **Frontend** — settings store (merge/persist/corrupt-JSON/pub-sub),
  credential headers, theme resolution + `.dark` toggling, and component
  rendering (SentimentPill, IndexCard) including click handling.

## Out of scope (Phase 2)

Harmonic patterns, option Greeks, and Fibonacci tooling are intentionally
**not** built.

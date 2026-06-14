import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import PageTransition from '../components/PageTransition.jsx'
import CandleChart from '../components/CandleChart.jsx'
import RSIPanel from '../components/RSIPanel.jsx'
import OITable from '../components/OITable.jsx'
import NewsFeed from '../components/NewsFeed.jsx'
import GreeksPanel from '../components/GreeksPanel.jsx'
import Harmonics from '../components/Harmonics.jsx'
import { Skeleton } from '../components/Skeleton.jsx'
import { getAnalysis } from '../api/client.js'
import { getSettings, INDICES, saveSettings } from '../store/settings.js'

const TIMEFRAMES = ['1H', '4H', '1D', '1W']

function MetricChip({ label, value, tone }) {
  return (
    <div className="card flex flex-col items-center px-3 py-2.5">
      <span className="text-[10px] font-bold uppercase tracking-wide text-muted">
        {label}
      </span>
      <span className={`text-sm font-bold ${tone || 'text-primary'}`}>
        {value}
      </span>
    </div>
  )
}

export default function Analysis() {
  const [symbol, setSymbol] = useState(getSettings().defaultIndex || 'NIFTY')
  const [timeframe, setTimeframe] = useState('1D')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let alive = true
    setData(null)
    setError(null)
    getAnalysis(symbol, timeframe)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e?.response?.data?.detail || 'Failed to load analysis'))
    return () => {
      alive = false
    }
  }, [symbol, timeframe])

  const onPickSymbol = (s) => {
    setSymbol(s)
    saveSettings({ defaultIndex: s })
  }

  return (
    <PageTransition title="Analysis" subtitle={`${symbol} · ${timeframe}`}>
      {error && (
        <div className="mb-3 rounded-xl bg-bearish/10 p-3 text-xs font-medium text-bearish">
          {error}
        </div>
      )}

      {/* Symbol selector */}
      <div className="no-scrollbar -mx-4 mb-3 flex gap-2 overflow-x-auto px-4">
        {INDICES.map((i) => (
          <button
            key={i.id}
            onClick={() => onPickSymbol(i.id)}
            className={`whitespace-nowrap rounded-full px-3.5 py-1.5 text-xs font-bold transition ${
              symbol === i.id
                ? 'btn-gloss'
                : 'bg-surface text-ink-soft'
            }`}
          >
            {i.label}
          </button>
        ))}
      </div>

      {/* Timeframe toggle */}
      <div className="mb-3 flex gap-1 rounded-xl bg-primary/5 p-1">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`relative flex-1 rounded-lg py-1.5 text-xs font-bold ${
              timeframe === tf ? 'text-white' : 'text-ink-soft'
            }`}
          >
            {timeframe === tf && (
              <motion.span
                layoutId="tfpill"
                className="absolute inset-0 rounded-lg bg-gloss-primary shadow-gloss"
              />
            )}
            <span className="relative">{tf}</span>
          </button>
        ))}
      </div>

      {/* Chart with Fibonacci overlay */}
      <div className="card mb-4 p-3">
        {data ? (
          <CandleChart candles={data.candles} fibLevels={data.fibonacci?.levels || []} />
        ) : (
          <Skeleton className="h-[320px] w-full rounded-lg" />
        )}
      </div>

      {/* Fibonacci summary */}
      {data?.fibonacci && (
        <div className="card mb-4 p-3.5">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-bold text-primary">Fibonacci</h3>
            <span className="text-2xs font-semibold text-muted">
              {data.fibonacci.direction === 'up' ? 'Up swing' : 'Down swing'} ·{' '}
              {data.fibonacci.low.toLocaleString('en-IN')}–
              {data.fibonacci.high.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {data.fibonacci.levels
              .filter((l) => l.kind === 'retracement')
              .map((l) => (
                <span
                  key={l.ratio}
                  className="rounded-md bg-neutral/10 px-2 py-0.5 text-[10px] font-semibold tabular-nums text-[#B45309]"
                >
                  {(l.ratio * 100).toFixed(1)}% · {l.price.toLocaleString('en-IN')}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* RSI */}
      <div className="mb-4">
        {data ? <RSIPanel rsi={data.rsi} /> : <Skeleton className="h-[160px] w-full rounded-2xl" />}
      </div>

      {/* OI metrics */}
      <h2 className="mb-2 text-xs font-bold uppercase tracking-wide text-muted">
        Options · Open Interest
      </h2>
      <div className="mb-3 grid grid-cols-3 gap-3">
        {data ? (
          <>
            <MetricChip
              label="PCR"
              value={data.oi.pcr?.toFixed(2)}
              tone={data.oi.pcr > 1 ? 'text-bullish' : 'text-bearish'}
            />
            <MetricChip label="Max Pain" value={data.oi.maxPain} />
            <MetricChip label="Spot" value={Math.round(data.oi.spot)} />
          </>
        ) : (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-[3.75rem] rounded-2xl" />
          ))
        )}
      </div>

      <div className="mb-4">
        {data ? (
          <OITable rows={data.oi.chain} spot={data.oi.spot} />
        ) : (
          <Skeleton className="h-64 w-full rounded-2xl" />
        )}
      </div>

      {/* Option Greeks */}
      <div className="mb-4">
        {data ? (
          <GreeksPanel greeks={data.greeks} />
        ) : (
          <Skeleton className="h-48 w-full rounded-2xl" />
        )}
      </div>

      {/* Harmonic patterns */}
      <h2 className="mb-2 text-xs font-bold uppercase tracking-wide text-muted">
        Harmonic Patterns
      </h2>
      <div className="mb-4">
        {data ? (
          <Harmonics patterns={data.harmonics} />
        ) : (
          <Skeleton className="h-20 w-full rounded-2xl" />
        )}
      </div>

      {/* News */}
      <h2 className="mb-2 text-xs font-bold uppercase tracking-wide text-muted">
        News · Groq sentiment
      </h2>
      {data ? (
        <NewsFeed items={data.news} />
      ) : (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-2xl" />
          ))}
        </div>
      )}
    </PageTransition>
  )
}

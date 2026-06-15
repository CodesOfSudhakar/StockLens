import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import PageTransition from '../components/PageTransition.jsx'
import IndexCard from '../components/IndexCard.jsx'
import SentimentPill from '../components/SentimentPill.jsx'
import { Skeleton, SkeletonCard } from '../components/Skeleton.jsx'
import { getOverview } from '../api/client.js'
import { saveSettings } from '../store/settings.js'

function Stat({ label, value, tone }) {
  return (
    <div className="card flex flex-col items-center justify-center px-2 py-3">
      <span className="text-[10px] font-bold uppercase tracking-wide text-muted">
        {label}
      </span>
      <span className={`mt-0.5 text-base font-bold ${tone || 'text-primary'}`}>
        {value}
      </span>
    </div>
  )
}

function Mover({ item, up }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm font-semibold text-ink">{item.symbol}</span>
      <span className={`text-sm font-bold ${up ? 'text-bullish' : 'text-bearish'}`}>
        {up ? '+' : ''}
        {item.changePct.toFixed(2)}%
      </span>
    </div>
  )
}

export default function Home() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    let alive = true
    getOverview()
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e?.response?.data?.detail || 'Failed to load market data'))
    return () => {
      alive = false
    }
  }, [])

  const openAnalysis = (symbol) => {
    saveSettings({ defaultIndex: symbol })
    navigate('/analysis')
  }

  return (
    <PageTransition
      brand
      title="StockLens"
      subtitle="Indian markets · live overview"
      action={
        data ? (
          <SentimentPill value={data.sentiment} label={data.sentimentLabel} />
        ) : (
          <Skeleton className="h-7 w-24 rounded-full" />
        )
      }
    >
      {error && (
        <div className="mb-3 rounded-xl bg-bearish/10 p-3 text-xs font-medium text-bearish">
          {error}
        </div>
      )}

      {/* Indices carousel */}
      <section className="mb-5">
        <h2 className="mb-2 text-xs font-bold uppercase tracking-wide text-muted">
          Indices
        </h2>
        <div className="no-scrollbar -mx-4 flex gap-3 overflow-x-auto px-4 pb-1">
          {data
            ? data.indices.map((idx) => (
                <IndexCard
                  key={idx.symbol}
                  index={idx}
                  onClick={() => openAnalysis(idx.symbol)}
                />
              ))
            : Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-[5.5rem] min-w-[9.5rem] rounded-2xl" />
              ))}
        </div>
      </section>

      {/* VIX + breadth */}
      <section className="mb-5 grid grid-cols-3 gap-3">
        {data ? (
          <>
            <Stat label="India VIX" value={data.vix?.toFixed(2)} tone="text-neutral" />
            <Stat
              label="Advances"
              value={data.breadth?.advances}
              tone="text-bullish"
            />
            <Stat
              label="Declines"
              value={data.breadth?.declines}
              tone="text-bearish"
            />
          </>
        ) : (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-[4.5rem] rounded-2xl" />
          ))
        )}
      </section>

      {/* Breadth bar */}
      {data && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-5"
        >
          <div className="mb-1 flex justify-between text-[10px] font-semibold text-muted">
            <span>Market breadth</span>
            <span>
              {(
                (data.breadth.advances /
                  (data.breadth.advances + data.breadth.declines)) *
                100
              ).toFixed(0)}
              % advancing
            </span>
          </div>
          <div className="flex h-2.5 overflow-hidden rounded-full bg-bearish/30">
            <motion.div
              initial={{ width: 0 }}
              animate={{
                width: `${
                  (data.breadth.advances /
                    (data.breadth.advances + data.breadth.declines)) *
                  100
                }%`,
              }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              className="h-full bg-bullish"
            />
          </div>
        </motion.div>
      )}

      {/* Gainers / Losers */}
      <section className="grid grid-cols-2 gap-3">
        {data ? (
          <>
            <div className="card p-3.5">
              <h3 className="mb-1 text-xs font-bold text-bullish">Top Gainers</h3>
              <div className="divide-y divide-line">
                {data.gainers.map((g) => (
                  <Mover key={g.symbol} item={g} up />
                ))}
              </div>
            </div>
            <div className="card p-3.5">
              <h3 className="mb-1 text-xs font-bold text-bearish">Top Losers</h3>
              <div className="divide-y divide-line">
                {data.losers.map((l) => (
                  <Mover key={l.symbol} item={l} up={false} />
                ))}
              </div>
            </div>
          </>
        ) : (
          <>
            <SkeletonCard />
            <SkeletonCard />
          </>
        )}
      </section>
    </PageTransition>
  )
}

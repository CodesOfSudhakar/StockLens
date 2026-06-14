import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import PageTransition from '../components/PageTransition.jsx'
import SentimentPill from '../components/SentimentPill.jsx'
import { Skeleton } from '../components/Skeleton.jsx'
import { runOutlook } from '../api/client.js'
import { getSettings, INDICES } from '../store/settings.js'

const AGENTS = [
  { key: 'technical', label: 'Technical Agent', hint: 'EMA stack · RSI · price action' },
  { key: 'oi', label: 'OI Agent', hint: 'PCR · Max Pain · buildups' },
  { key: 'news', label: 'News Agent', hint: 'Groq headline sentiment' },
  { key: 'supervisor', label: 'Supervisor', hint: 'Synthesises final call' },
]

function ResultRow({ label, value, tone }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-line py-2.5 last:border-0">
      <span className="text-xs font-bold uppercase tracking-wide text-muted">
        {label}
      </span>
      <span className={`text-right text-sm font-semibold ${tone || 'text-ink'}`}>
        {value}
      </span>
    </div>
  )
}

export default function AIOutlook() {
  const [symbol, setSymbol] = useState(getSettings().defaultIndex || 'NIFTY')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const run = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const d = await runOutlook(symbol)
      setResult(d)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Pipeline failed. Check Groq API key in Settings.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageTransition title="AI Outlook" subtitle="LangGraph multi-agent pipeline">
      {/* Symbol picker */}
      <div className="no-scrollbar -mx-4 mb-4 flex gap-2 overflow-x-auto px-4">
        {INDICES.map((i) => (
          <button
            key={i.id}
            onClick={() => setSymbol(i.id)}
            disabled={loading}
            className={`whitespace-nowrap rounded-full px-3.5 py-1.5 text-xs font-bold transition ${
              symbol === i.id ? 'btn-gloss' : 'bg-surface text-ink-soft'
            }`}
          >
            {i.label}
          </button>
        ))}
      </div>

      {/* Run button */}
      <motion.button
        whileTap={{ scale: 0.97 }}
        onClick={run}
        disabled={loading}
        className="mb-5 w-full rounded-2xl btn-gloss py-4 text-base font-bold text-white shadow-card disabled:opacity-60"
      >
        {loading ? 'Running pipeline…' : `Analyse ${symbol}`}
      </motion.button>

      {error && (
        <div className="mb-4 rounded-xl bg-bearish/10 p-3 text-xs font-medium text-bearish">
          {error}
        </div>
      )}

      {/* Agent pipeline status */}
      {loading && (
        <div className="mb-5 space-y-2">
          {AGENTS.map((a, i) => (
            <motion.div
              key={a.key}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.15 }}
              className="card flex items-center gap-3 p-3"
            >
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-neutral opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-neutral" />
              </span>
              <div className="flex-1">
                <p className="text-sm font-bold text-primary">{a.label}</p>
                <p className="text-[11px] text-muted">{a.hint}</p>
              </div>
              <Skeleton className="h-3 w-10" />
            </motion.div>
          ))}
        </div>
      )}

      {/* Result */}
      <AnimatePresence>
        {result && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="card p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-bold text-primary">Final Call</h2>
                <SentimentPill value={result.bias} label={result.bias} />
              </div>
              <ResultRow label="Bias" value={result.bias} />
              <ResultRow label="Expected Range" value={result.range} />
              <ResultRow label="Key Levels" value={result.keyLevels} />
              <ResultRow label="Risk" value={result.risk} tone="text-bearish" />
              {result.confidence != null && (
                <ResultRow label="Confidence" value={`${result.confidence}%`} tone="text-neutral" />
              )}
            </div>

            {result.summary && (
              <div className="card p-4">
                <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-muted">
                  Supervisor Summary
                </h3>
                <p className="text-sm leading-relaxed text-ink">{result.summary}</p>
              </div>
            )}

            {/* Per-agent breakdown */}
            {result.agents &&
              AGENTS.filter((a) => a.key !== 'supervisor').map((a) => {
                const out = result.agents[a.key]
                if (!out) return null
                return (
                  <div key={a.key} className="card p-4">
                    <div className="mb-1 flex items-center justify-between">
                      <h3 className="text-sm font-bold text-primary">{a.label}</h3>
                      {out.signal && <SentimentPill value={out.signal} label={out.signal} />}
                    </div>
                    <p className="text-xs leading-relaxed text-ink-soft">{out.reasoning}</p>
                  </div>
                )
              })}

            <p className="px-1 pb-2 text-center text-[10px] text-muted">
              For research only. Not investment advice.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {!result && !loading && !error && (
        <div className="card p-5 text-center">
          <p className="text-sm font-semibold text-primary">
            Three agents, one verdict.
          </p>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            Technical, OI, and News agents each analyse {symbol}; the Supervisor
            synthesises a single bias, range, key levels, and risk.
          </p>
        </div>
      )}
    </PageTransition>
  )
}

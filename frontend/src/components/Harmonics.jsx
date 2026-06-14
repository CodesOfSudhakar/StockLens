import SentimentPill from './SentimentPill.jsx'

// Detected harmonic patterns (Gartley / Bat / Butterfly / Crab), or an
// explicit "none" state — these patterns are genuinely rare.
export default function Harmonics({ patterns = [] }) {
  if (!patterns.length) {
    return (
      <div className="card p-4 text-center">
        <p className="text-xs font-medium text-muted">
          No harmonic patterns detected in the current swing structure.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {patterns.map((p, i) => (
        <div key={i} className="card p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-bold text-primary">{p.name}</h3>
            <SentimentPill value={p.direction} label={p.direction} />
          </div>
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="font-semibold text-muted">Reversal zone (D)</span>
            <span className="font-bold tabular-nums text-ink">{p.prz.toLocaleString('en-IN')}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(p.points).map(([k, v]) => (
              <span
                key={k}
                className="rounded-md bg-ink/5 px-2 py-0.5 text-[10px] font-semibold text-ink-soft tabular-nums"
              >
                {k} {v.toLocaleString('en-IN')}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

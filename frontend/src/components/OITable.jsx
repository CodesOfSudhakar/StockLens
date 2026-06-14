// Option-chain OI table with CE/PE buildup classification.
const BUILDUP_STYLE = {
  'Long Buildup': 'bg-bullish/15 text-bullish',
  'Short Covering': 'bg-bullish/10 text-bullish',
  'Long Unwinding': 'bg-bearish/10 text-bearish',
  'Short Buildup': 'bg-bearish/15 text-bearish',
}

function compact(n) {
  if (n == null) return '—'
  const a = Math.abs(n)
  if (a >= 1e7) return (n / 1e7).toFixed(1) + 'Cr'
  if (a >= 1e5) return (n / 1e5).toFixed(1) + 'L'
  if (a >= 1e3) return (n / 1e3).toFixed(1) + 'K'
  return String(n)
}

function Buildup({ value }) {
  if (!value) return <span className="text-muted">—</span>
  return (
    <span className={`pill px-2 py-0.5 text-[10px] ${BUILDUP_STYLE[value] || ''}`}>
      {value}
    </span>
  )
}

export default function OITable({ rows = [], spot }) {
  return (
    <div className="card overflow-hidden">
      <div className="grid grid-cols-[1fr_auto_1fr] border-b border-line bg-primary/5 px-3 py-2 text-[10px] font-bold uppercase tracking-wide text-primary">
        <span>Calls (CE)</span>
        <span className="px-2 text-center">Strike</span>
        <span className="text-right">Puts (PE)</span>
      </div>
      <div className="divide-y divide-line">
        {rows.map((r) => {
          const atm = spot != null && Math.abs(r.strike - spot) <= (r.step || 50) / 2
          return (
            <div
              key={r.strike}
              className={`grid grid-cols-[1fr_auto_1fr] items-center px-3 py-2 text-xs ${
                atm ? 'bg-neutral/10' : ''
              }`}
            >
              <div className="flex flex-col gap-1">
                <span className="font-semibold text-ink">
                  OI {compact(r.ceOi)}
                </span>
                <Buildup value={r.ceBuildup} />
              </div>
              <span className="px-2 text-center text-sm font-bold text-primary">
                {r.strike}
              </span>
              <div className="flex flex-col items-end gap-1">
                <span className="font-semibold text-ink">
                  OI {compact(r.peOi)}
                </span>
                <Buildup value={r.peBuildup} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

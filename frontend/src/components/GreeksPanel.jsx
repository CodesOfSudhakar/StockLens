// Option Greeks for a band of strikes around ATM (CE focus, PE delta).
function Cell({ children, className = '' }) {
  return <td className={`py-1.5 text-right tabular-nums ${className}`}>{children}</td>
}

export default function GreeksPanel({ greeks }) {
  if (!greeks || !greeks.rows?.length) return null
  const { sigma, tDays, r, atm, rows } = greeks

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2">
        <h3 className="text-sm font-bold text-primary">Option Greeks</h3>
        <span className="text-2xs font-semibold text-muted">
          σ {(sigma * 100).toFixed(1)}% · {tDays}d · r {(r * 100).toFixed(1)}%
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-2xs">
          <thead>
            <tr className="text-muted">
              <th className="py-1.5 pl-3 text-left font-bold uppercase tracking-wide">Strike</th>
              <th className="py-1.5 text-right font-bold">Δ CE</th>
              <th className="py-1.5 text-right font-bold">Δ PE</th>
              <th className="py-1.5 text-right font-bold">Γ</th>
              <th className="py-1.5 text-right font-bold">Θ CE</th>
              <th className="py-1.5 pr-3 text-right font-bold">V</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((row) => {
              const isAtm = row.strike === atm
              return (
                <tr
                  key={row.strike}
                  className={isAtm ? 'bg-neutral/10 font-semibold text-ink' : 'text-ink-soft'}
                >
                  <td className="py-1.5 pl-3 text-left font-bold text-ink">{row.strike}</td>
                  <Cell className="text-bullish">{row.ce.delta.toFixed(2)}</Cell>
                  <Cell className="text-bearish">{row.pe.delta.toFixed(2)}</Cell>
                  <Cell>{row.ce.gamma.toFixed(4)}</Cell>
                  <Cell>{row.ce.theta.toFixed(1)}</Cell>
                  <td className="py-1.5 pr-3 text-right tabular-nums">{row.ce.vega.toFixed(1)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="px-3 py-2 text-[10px] leading-relaxed text-muted">
        Δ delta · Γ gamma · Θ theta/day · V vega per 1% vol. Computed via
        Black-Scholes at realised volatility (σ).
      </p>
    </div>
  )
}

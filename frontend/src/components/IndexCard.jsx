import { motion } from 'framer-motion'

function fmt(n) {
  return Number(n).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export default function IndexCard({ index, onClick }) {
  const up = index.change >= 0
  const color = up ? 'text-bullish' : 'text-bearish'
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className="card flex min-w-[8.75rem] flex-col items-start p-3 text-left"
    >
      <span className="text-2xs font-semibold uppercase tracking-wider text-muted">
        {index.label}
      </span>
      <span className="mt-1.5 text-[15px] font-bold tracking-tight text-ink">
        {fmt(index.ltp)}
      </span>
      <span className={`mt-1 text-2xs font-semibold ${color}`}>
        {up ? '▲' : '▼'} {fmt(Math.abs(index.change))} ({up ? '+' : ''}
        {index.changePct?.toFixed(2)}%)
      </span>
    </motion.button>
  )
}

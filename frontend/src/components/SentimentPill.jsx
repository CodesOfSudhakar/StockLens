// Maps a sentiment / bias string to a coloured pill.
const STYLES = {
  bullish: 'bg-bullish/15 text-bullish',
  positive: 'bg-bullish/15 text-bullish',
  bearish: 'bg-bearish/15 text-bearish',
  negative: 'bg-bearish/15 text-bearish',
  neutral: 'bg-neutral/15 text-[#B45309]',
}

const DOT = {
  bullish: 'bg-bullish',
  positive: 'bg-bullish',
  bearish: 'bg-bearish',
  negative: 'bg-bearish',
  neutral: 'bg-neutral',
}

export default function SentimentPill({ value = 'neutral', label }) {
  const key = String(value).toLowerCase()
  const cls = STYLES[key] || STYLES.neutral
  const dot = DOT[key] || DOT.neutral
  return (
    <span className={`pill ${cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label || value}
    </span>
  )
}

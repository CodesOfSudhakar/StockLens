import SentimentPill from './SentimentPill.jsx'

function ago(ts) {
  if (!ts) return ''
  const diff = (Date.now() - new Date(ts).getTime()) / 60000
  if (diff < 1) return 'just now'
  if (diff < 60) return `${Math.round(diff)}m ago`
  if (diff < 1440) return `${Math.round(diff / 60)}h ago`
  return `${Math.round(diff / 1440)}d ago`
}

export default function NewsFeed({ items = [] }) {
  if (!items.length) {
    return (
      <p className="px-1 py-6 text-center text-xs text-muted">
        No recent headlines.
      </p>
    )
  }
  return (
    <ul className="space-y-2">
      {items.map((n, i) => (
        <li key={i} className="card p-3.5">
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">
              {n.source || 'News'} · {ago(n.publishedAt)}
            </span>
            <SentimentPill value={n.sentiment} />
          </div>
          <p className="text-sm font-semibold leading-snug text-ink">
            {n.title}
          </p>
          {n.summary && (
            <p className="mt-1 text-xs leading-relaxed text-ink-soft">
              {n.summary}
            </p>
          )}
        </li>
      ))}
    </ul>
  )
}

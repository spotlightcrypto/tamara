import { Link } from 'react-router-dom'
import { formatDate, timeAgo } from './lib/time'
import type { NarrativeWithCompanies } from './lib/types'

export function NarrativeCard({
  n,
  creatorEmail,
}: {
  n: NarrativeWithCompanies
  creatorEmail?: string
}) {
  return (
    <Link
      to={`/narratives/${n.id}`}
      className="block border-2 border-ink bg-surface shadow-hard transition-all hover:-translate-x-[2px] hover:-translate-y-[2px] hover:shadow-hard-lg"
    >
      <div className="p-4">
        <h2 className="font-display text-xl font-bold tracking-tight">{n.title}</h2>
        {n.thesis && (
          <p className="mt-1.5 line-clamp-3 text-sm leading-relaxed text-muted">{n.thesis}</p>
        )}
        {n.companies.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {n.companies.map((c) => (
              <span
                key={c.id}
                className="border-2 border-ink bg-concrete px-2 py-0.5 font-mono text-xs font-bold"
              >
                {c.symbol}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 border-t-2 border-ink px-4 py-2 font-mono text-[0.68rem] uppercase tracking-wide text-muted">
        {creatorEmail && <span>◆ {creatorEmail}</span>}
        <span>created {formatDate(n.created_at)}</span>
        <span>updated {timeAgo(n.updated_at)}</span>
      </div>
    </Link>
  )
}

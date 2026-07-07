import { Link } from 'react-router-dom'
import { Label } from './ui'
import { formatDate, timeAgo } from './lib/time'
import type { NarrativeWithCompanies } from './lib/types'

export function NarrativeCard({ n }: { n: NarrativeWithCompanies }) {
  return (
    <article
      className={`border-2 border-ink bg-surface shadow-hard ${
        n.is_active ? '' : 'opacity-60'
      }`}
    >
      <div className="p-4">
        <div className="flex items-start gap-2">
          {/* Only the title navigates to the narrative — not the whole card. */}
          <h2 className="font-display text-xl font-bold tracking-tight">
            <Link
              to={`/narratives/${n.id}`}
              className="decoration-acid decoration-2 underline-offset-4 hover:underline"
            >
              {n.title}
            </Link>
          </h2>
          {!n.is_active && (
            <span className="mt-1 shrink-0 border-2 border-ink bg-concrete px-1.5 py-0.5 font-mono text-[0.6rem] font-bold uppercase tracking-wide text-muted">
              Inactive
            </span>
          )}
        </div>
        {n.thesis && (
          <p className="mt-1.5 line-clamp-3 text-sm leading-relaxed text-muted">{n.thesis}</p>
        )}
        {n.companies.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            {n.companies.map((c) => (
              // Each ticker navigates to that company's page.
              <Link
                key={c.id}
                to={`/companies/${c.slug}`}
                className="border-2 border-ink bg-concrete px-2 py-0.5 font-mono text-xs font-bold transition-all hover:bg-acid"
              >
                {c.symbol}
              </Link>
            ))}
          </div>
        )}
      </div>
      {/* Footer: username first (no @), positioning tag last on the line */}
      <div className="flex items-center justify-between gap-3 border-t-2 border-ink px-4 py-2 font-mono text-[0.68rem] uppercase tracking-wide text-muted">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5">
          {n.author_username && <span className="text-ink">{n.author_username}</span>}
          <span>created {formatDate(n.created_at)}</span>
          <span>updated {timeAgo(n.updated_at)}</span>
        </div>
        {n.positioning && <Label>{n.positioning}</Label>}
      </div>
    </article>
  )
}

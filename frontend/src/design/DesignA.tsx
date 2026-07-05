// Option A — DOSSIER: the whole narrative in one hard frame; masthead up top,
// body + an interior right rail (quotes, sources), notes at the foot. Internal
// hairlines instead of separate boxes. Mobile: the rail stacks under the body.
import { Link } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { Markdown } from '../Markdown'
import { formatDateTime, timeAgo } from '../lib/time'
import { type DesignData, Notes, QuoteCard, StatusToggle } from './shared'

export function DesignA({ d }: { d: DesignData }) {
  const { narrative: n, companies, sources, notes, quotes, username } = d
  const hasRail = companies.length > 0 || sources.length > 0

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <div className="border-2 border-ink bg-surface shadow-hard">
        {/* Masthead */}
        <div className="border-b-2 border-ink p-5">
          <div className="flex items-start justify-between gap-3">
            <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">{n.title}</h1>
            <StatusToggle narrative={n} onToggle={d.onToggleActive} busy={d.togglingActive} />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {n.positioning && (
              <span className="border-2 border-ink bg-acid px-2 py-0.5 font-mono text-xs font-bold uppercase">
                {n.positioning}
              </span>
            )}
            {companies.map((c) => (
              <Link
                key={c.id}
                to={`/companies/${c.id}`}
                className="border-2 border-ink bg-surface px-2 py-0.5 font-mono text-xs font-bold hover:bg-acid"
              >
                {c.symbol}
              </Link>
            ))}
          </div>
          <p className="mt-2 font-mono text-[0.68rem] uppercase tracking-wide text-muted">
            created by {username} · {formatDateTime(n.created_at)} · updated {timeAgo(n.updated_at)}
          </p>
        </div>

        {/* Body + interior rail */}
        <div className="lg:flex">
          <div className="min-w-0 flex-1 p-5">
            {n.thesis && <p className="max-w-prose leading-relaxed">{n.thesis}</p>}
            {n.body_md && (
              <div className="mt-5">
                <Markdown>{n.body_md}</Markdown>
              </div>
            )}
          </div>

          {hasRail && (
            <aside className="shrink-0 border-t-2 border-ink lg:w-64 lg:border-l-2 lg:border-t-0">
              {companies.length > 0 && (
                <div className="space-y-4 border-b-2 border-ink p-4">
                  <div className="text-[0.62rem] font-bold uppercase tracking-widest text-muted">Quotes</div>
                  {companies.map((c) => (
                    <QuoteCard key={c.id} company={c} q={quotes[c.id]} />
                  ))}
                </div>
              )}
              {sources.length > 0 && (
                <div className="p-4">
                  <div className="mb-2 text-[0.62rem] font-bold uppercase tracking-widest text-muted">Sources</div>
                  <div className="space-y-1.5">
                    {sources.map((s) => (
                      <a
                        key={s.id}
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs hover:bg-acid"
                      >
                        <ExternalLink size={11} strokeWidth={2.5} className="shrink-0" />
                        <span className="truncate">{s.title || s.url}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </aside>
          )}
        </div>

        {/* Notes */}
        <div className="border-t-2 border-ink p-5">
          <div className="mb-2 text-[0.62rem] font-bold uppercase tracking-widest text-muted">
            Notes · {notes.length}
          </div>
          <Notes notes={notes} onAdd={d.onAddNote} />
        </div>
      </div>
    </main>
  )
}

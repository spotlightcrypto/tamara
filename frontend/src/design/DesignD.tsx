// Option D — TICKER: quotes as a horizontal tape under the masthead, freeing the
// body to be a single full-width unboxed reading column. Sources inline footer.
// Mobile: the tape scrolls horizontally; the body already flows full-width.
import { Link } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { Markdown } from '../Markdown'
import { formatDateTime, timeAgo } from '../lib/time'
import { type DesignData, Notes, StatusToggle, WINDOWS, fmtPct, pctClass } from './shared'

export function DesignD({ d }: { d: DesignData }) {
  const { narrative: n, companies, sources, notes, quotes, username } = d

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <div className="flex items-start justify-between gap-3">
        <div>
          {n.positioning && (
            <div className="mb-2">
              <span className="border-2 border-ink bg-acid px-2 py-0.5 font-mono text-xs font-bold uppercase">
                {n.positioning}
              </span>
            </div>
          )}
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{n.title}</h1>
        </div>
        <StatusToggle narrative={n} onToggle={d.onToggleActive} busy={d.togglingActive} />
      </div>
      <p className="mt-2 font-mono text-[0.68rem] uppercase tracking-wide text-muted">
        created by {username} · {formatDateTime(n.created_at)} · updated {timeAgo(n.updated_at)}
      </p>

      {/* Ticker tape */}
      {companies.length > 0 && (
        <div className="mt-4 overflow-x-auto border-2 border-ink bg-surface shadow-hard">
          <div className="min-w-max divide-y-2 divide-ink">
            {companies.map((c) => {
              const p = quotes[c.id]
              return (
                <div key={c.id} className="flex items-center gap-4 whitespace-nowrap px-3 py-2 font-mono text-xs">
                  <Link
                    to={`/companies/${c.id}`}
                    className="border-2 border-ink bg-concrete px-2 py-0.5 font-bold hover:bg-acid"
                  >
                    {c.symbol}
                  </Link>
                  {WINDOWS.map((w) => (
                    <span key={w}>
                      <span className="text-muted">{w} </span>
                      <span className={pctClass(p?.performance?.[w])}>{fmtPct(p?.performance?.[w])}</span>
                    </span>
                  ))}
                  {typeof p?.since_close === 'number' && (
                    <span className="border-l-2 border-ink pl-4 text-muted">
                      @cr ${p.since_close.toFixed(2)}{' '}
                      <span className={pctClass(p.since_change)}>({fmtPct(p.since_change)})</span>
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Full-width unboxed body */}
      {n.thesis && <p className="mt-6 text-lg leading-relaxed">{n.thesis}</p>}
      {n.body_md && (
        <div className="mt-4">
          <Markdown>{n.body_md}</Markdown>
        </div>
      )}

      {sources.length > 0 && (
        <div className="mt-8 flex flex-wrap items-center gap-x-3 gap-y-1 border-t-2 border-ink pt-3">
          <span className="font-mono text-[0.62rem] font-bold uppercase tracking-widest text-muted">Sources</span>
          {sources.map((s) => (
            <a
              key={s.id}
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs underline decoration-acid decoration-2 underline-offset-2 hover:bg-acid"
            >
              <ExternalLink size={11} strokeWidth={2.5} /> {s.title || s.url}
            </a>
          ))}
        </div>
      )}

      <div className="mt-8 border-t-2 border-ink pt-4">
        <div className="mb-2 font-mono text-[0.62rem] font-bold uppercase tracking-widest text-muted">
          Notes · {notes.length}
        </div>
        <Notes notes={notes} onAdd={d.onAddNote} />
      </div>
    </main>
  )
}

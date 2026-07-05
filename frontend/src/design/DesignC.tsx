// Option C — TERMINAL: one instrument. A dark masthead bar, then a grid of cells
// that share borders (body | quotes/sources), notes across the foot. Dense,
// unmistakably brutalist. Mobile: the grid collapses to stacked cells.
import { Link } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { Markdown } from '../Markdown'
import { formatDateTime, timeAgo } from '../lib/time'
import { type DesignData, Notes, QuoteCard } from './shared'

function Label({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block bg-acid px-1.5 py-0.5 font-mono text-[0.6rem] font-bold uppercase tracking-widest text-ink">
      {children}
    </span>
  )
}

export function DesignC({ d }: { d: DesignData }) {
  const { narrative: n, companies, sources, notes, quotes, username } = d

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="border-2 border-ink shadow-hard">
        {/* Dark masthead */}
        <div className="bg-ink px-4 py-3">
          <div className="flex items-start justify-between gap-3">
            <h1 className="font-display text-xl font-bold tracking-tight text-surface sm:text-2xl">{n.title}</h1>
            <div className="shrink-0 text-right font-mono text-[0.62rem] uppercase tracking-wide">
              <div className={n.is_active ? 'text-acid' : 'text-surface/50'}>
                {n.is_active ? '● Active' : '○ Inactive'}
              </div>
              <button
                onClick={d.onToggleActive}
                disabled={d.togglingActive}
                className="text-[0.6rem] text-surface/60 underline decoration-dotted hover:text-acid disabled:opacity-50"
              >
                {n.is_active ? 'retire' : 'reactivate'}
              </button>
            </div>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[0.62rem] uppercase tracking-wide">
            {n.positioning && <span className="bg-acid px-1.5 py-0.5 font-bold text-ink">{n.positioning}</span>}
            {companies.map((c) => (
              <Link key={c.id} to={`/companies/${c.id}`} className="text-surface hover:text-acid">
                {c.symbol}
              </Link>
            ))}
            <span className="text-surface/50">
              created by {username} · {formatDateTime(n.created_at)} · upd {timeAgo(n.updated_at)}
            </span>
          </div>
        </div>

        {/* Body | rail grid */}
        <div className="bg-surface lg:grid lg:grid-cols-[1fr_16rem]">
          <div className="border-b-2 border-ink p-4 lg:border-b-0 lg:border-r-2">
            {n.thesis && <p className="max-w-prose leading-relaxed">{n.thesis}</p>}
            {n.body_md && (
              <div className="mt-4">
                <Markdown>{n.body_md}</Markdown>
              </div>
            )}
          </div>
          <div>
            {companies.length > 0 && (
              <div className="space-y-4 border-b-2 border-ink p-3">
                <Label>Quotes</Label>
                {companies.map((c) => (
                  <QuoteCard key={c.id} company={c} q={quotes[c.id]} />
                ))}
              </div>
            )}
            {sources.length > 0 && (
              <div className="space-y-1.5 p-3">
                <Label>Sources</Label>
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
            )}
          </div>
        </div>

        {/* Notes cell */}
        <div className="space-y-2 border-t-2 border-ink bg-surface p-4">
          <Label>Notes · {notes.length}</Label>
          <Notes notes={notes} onAdd={d.onAddNote} />
        </div>
      </div>
    </main>
  )
}

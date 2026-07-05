// Option B — EDITORIAL: the body is NOT in a box; title → summary → body read as
// one continuous article. Quotes are a slim, quiet rail (sticky on desktop; a
// compact block at the top on mobile). Sources are a footer rule. Minimal
// framing; hierarchy comes from type + whitespace.
import { Link } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { Markdown } from '../Markdown'
import { formatDateTime, timeAgo } from '../lib/time'
import { type DesignData, Notes, QuoteCard, StatusToggle } from './shared'

export function DesignB({ d }: { d: DesignData }) {
  const { narrative: n, companies, sources, notes, quotes, username } = d

  const rail = companies.length > 0 && (
    <div className="border-2 border-ink bg-surface">
      <div className="border-b-2 border-ink bg-concrete px-3 py-1 text-[0.62rem] font-bold uppercase tracking-widest text-muted">
        Quotes
      </div>
      <div className="space-y-4 p-3">
        {companies.map((c) => (
          <QuoteCard key={c.id} company={c} q={quotes[c.id]} />
        ))}
      </div>
    </div>
  )

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <div className="lg:flex lg:gap-10">
        <article className="min-w-0 lg:max-w-2xl lg:flex-1">
          <div className="flex items-start justify-between gap-3">
            <div>
              {n.positioning && (
                <div className="mb-2">
                  <span className="bg-acid px-1.5 py-0.5 font-mono text-xs font-bold uppercase tracking-widest text-ink">
                    {n.positioning}
                  </span>
                </div>
              )}
              <h1 className="font-display text-3xl font-bold leading-[1.05] tracking-tight sm:text-4xl">
                {n.title}
              </h1>
            </div>
            <StatusToggle narrative={n} onToggle={d.onToggleActive} busy={d.togglingActive} />
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-1.5">
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

          {/* Quotes appear here on mobile only */}
          <div className="mt-6 lg:hidden">{rail}</div>

          <hr className="mt-6 border-0 border-t-2 border-ink" />
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
        </article>

        {/* Slim rail — desktop only */}
        <aside className="hidden self-start lg:sticky lg:top-16 lg:block lg:w-56">{rail}</aside>
      </div>
    </main>
  )
}

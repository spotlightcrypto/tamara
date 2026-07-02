import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from './lib/api'
import { Header } from './Header'
import { formatDate, timeAgo } from './lib/time'
import type { Company, Item, ItemKind, Narrative, Note } from './lib/types'

const SECTIONS: { kind: ItemKind; label: string }[] = [
  { kind: 'bull', label: 'Bull case' },
  { kind: 'bear', label: 'Bear case' },
  { kind: 'catalyst', label: 'Catalysts' },
  { kind: 'risk', label: 'Risks' },
]

export function NarrativeDetail() {
  const { id } = useParams<{ id: string }>()
  const [narrative, setNarrative] = useState<Narrative | null>(null)
  const [items, setItems] = useState<Item[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const [n, its, cos, nts] = await Promise.all([
          api.get<Narrative>(`/narratives/${id}`),
          api.get<Item[]>(`/narratives/${id}/items`),
          api.get<Company[]>(`/narratives/${id}/companies`),
          api.get<Note[]>(`/narratives/${id}/notes`),
        ])
        setNarrative(n)
        setItems(its)
        setCompanies(cos)
        setNotes(nts)
      } catch {
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <Link to="/" className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-muted hover:text-ink">
          <ArrowLeft size={14} strokeWidth={2.5} /> Back
        </Link>

        {loading && <p className="mt-6 text-sm uppercase tracking-wide text-muted">Loading…</p>}
        {!loading && notFound && (
          <p className="mt-6 border-2 border-dashed border-ink p-8 text-center text-sm uppercase tracking-wide text-muted">
            Narrative not found.
          </p>
        )}

        {narrative && (
          <>
            <h1 className="mt-4 font-display text-3xl font-bold tracking-tight">{narrative.title}</h1>
            {companies.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {companies.map((c) => (
                  <span key={c.id} className="border-2 border-ink bg-surface px-2 py-0.5 font-mono text-xs font-bold">
                    {c.symbol}
                  </span>
                ))}
              </div>
            )}
            {narrative.thesis && (
              <p className="mt-4 max-w-prose leading-relaxed">{narrative.thesis}</p>
            )}

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {SECTIONS.map(({ kind, label }) => {
                const pts = items.filter((i) => i.kind === kind).sort((a, b) => a.position - b.position)
                return (
                  <section key={kind} className="border-2 border-ink bg-surface shadow-hard">
                    <div className="border-b-2 border-ink bg-acid px-3 py-1 text-xs font-bold uppercase tracking-widest">
                      {label} · {pts.length}
                    </div>
                    <ul className="space-y-2 p-3">
                      {pts.length === 0 && <li className="text-xs uppercase tracking-wide text-muted">—</li>}
                      {pts.map((it) => (
                        <li key={it.id} className="text-sm leading-relaxed">
                          <span className="mr-1 text-acid">▸</span>
                          {it.body}
                          {it.event_date && (
                            <span className="ml-1 font-mono text-xs text-muted">({it.event_date})</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </section>
                )
              })}
            </div>

            {notes.length > 0 && (
              <section className="mt-4 border-2 border-ink bg-surface shadow-hard">
                <div className="border-b-2 border-ink bg-acid px-3 py-1 text-xs font-bold uppercase tracking-widest">
                  Notes · {notes.length}
                </div>
                <ul className="space-y-2 p-3">
                  {notes.map((n) => (
                    <li key={n.id} className="text-sm leading-relaxed text-muted">{n.body}</li>
                  ))}
                </ul>
              </section>
            )}

            <p className="mt-6 font-mono text-[0.68rem] uppercase tracking-wide text-muted">
              created {formatDate(narrative.created_at)} · updated {timeAgo(narrative.updated_at)}
            </p>
          </>
        )}
      </main>
    </div>
  )
}

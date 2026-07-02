import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { api } from './lib/api'
import { Header } from './Header'
import { formatDate, timeAgo } from './lib/time'
import type { Company, Item, ItemKind, Narrative, Note, Source } from './lib/types'

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
  const [sources, setSources] = useState<Source[]>([])
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  const [noteBody, setNoteBody] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [togglingActive, setTogglingActive] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const [n, its, cos, srcs, nts] = await Promise.all([
          api.get<Narrative>(`/narratives/${id}`),
          api.get<Item[]>(`/narratives/${id}/items`),
          api.get<Company[]>(`/narratives/${id}/companies`),
          api.get<Source[]>(`/narratives/${id}/sources`),
          api.get<Note[]>(`/narratives/${id}/notes`),
        ])
        setNarrative(n)
        setItems(its)
        setCompanies(cos)
        setSources(srcs)
        setNotes(nts)
      } catch {
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  async function toggleActive() {
    if (!narrative) return
    setTogglingActive(true)
    try {
      const updated = await api.patch<Narrative>(`/narratives/${id}`, {
        is_active: !narrative.is_active,
      })
      setNarrative(updated)
    } finally {
      setTogglingActive(false)
    }
  }

  async function addNote(e: React.FormEvent) {
    e.preventDefault()
    const body = noteBody.trim()
    if (!body) return
    setSavingNote(true)
    try {
      const note = await api.post<Note>(`/narratives/${id}/notes`, { body })
      setNotes((prev) => [note, ...prev])
      setNoteBody('')
    } finally {
      setSavingNote(false)
    }
  }

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-muted hover:text-ink"
        >
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
            <div className="mt-4 flex items-start justify-between gap-3">
              <h1 className="font-display text-3xl font-bold tracking-tight">
                {narrative.title}
              </h1>
              {/* Owner-only status: only the owner can load this narrative (RLS),
                  so reaching this page means you own it. Status is plain text;
                  the retire/reactivate action is a small text link beneath it. */}
              <div className="mt-1.5 shrink-0 text-right font-mono text-[0.68rem] uppercase tracking-wide">
                <div className={narrative.is_active ? 'text-ink' : 'text-muted'}>
                  {narrative.is_active ? '● Active' : '○ Inactive'}
                </div>
                <button
                  onClick={toggleActive}
                  disabled={togglingActive}
                  className="mt-0.5 text-[0.62rem] text-muted underline decoration-dotted underline-offset-2 hover:text-ink disabled:opacity-50"
                >
                  {narrative.is_active ? 'retire' : 'reactivate'}
                </button>
              </div>
            </div>
            {companies.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {companies.map((c) => (
                  <Link
                    key={c.id}
                    to={`/companies/${c.id}`}
                    className="border-2 border-ink bg-surface px-2 py-0.5 font-mono text-xs font-bold transition-all hover:bg-acid"
                  >
                    {c.symbol}
                  </Link>
                ))}
              </div>
            )}
            {narrative.thesis && (
              <p className="mt-4 max-w-prose leading-relaxed">{narrative.thesis}</p>
            )}

            {sources.length > 0 && (
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="font-mono text-[0.62rem] font-bold uppercase tracking-widest text-muted">
                  Sources
                </span>
                {sources.map((s) => (
                  <a
                    key={s.id}
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    title={s.url}
                    className="inline-flex max-w-xs items-center gap-1 border-2 border-ink bg-surface px-2 py-0.5 text-xs font-medium shadow-hard transition-all hover:bg-acid"
                  >
                    <ExternalLink size={12} strokeWidth={2.5} className="shrink-0" />
                    <span className="truncate">{s.title || s.url}</span>
                  </a>
                ))}
              </div>
            )}

            <div className="mt-8 space-y-4">
              {SECTIONS.map(({ kind, label }) => {
                const pts = items
                  .filter((i) => i.kind === kind)
                  .sort((a, b) => a.position - b.position)
                return (
                  <section key={kind} className="border-2 border-ink bg-surface shadow-hard">
                    <div className="border-b-2 border-ink bg-acid px-3 py-1 text-xs font-bold uppercase tracking-widest">
                      {label} · {pts.length}
                    </div>
                    <ul className="space-y-2 p-3">
                      {pts.length === 0 && (
                        <li className="text-xs uppercase tracking-wide text-muted">—</li>
                      )}
                      {pts.map((it) => (
                        <li key={it.id} className="text-sm leading-relaxed">
                          <span className="mr-1 text-acid">▸</span>
                          {it.body}
                          {it.event_date && (
                            <span className="ml-1 font-mono text-xs text-muted">
                              ({it.event_date})
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </section>
                )
              })}
            </div>

            {/* Notes — post-publication commentary, added here after the narrative exists. */}
            <section className="mt-4 border-2 border-ink bg-surface shadow-hard">
              <div className="border-b-2 border-ink bg-acid px-3 py-1 text-xs font-bold uppercase tracking-widest">
                Notes · {notes.length}
              </div>
              <div className="p-3">
                <form onSubmit={addNote} className="mb-3">
                  <textarea
                    value={noteBody}
                    onChange={(e) => setNoteBody(e.target.value)}
                    rows={2}
                    placeholder="Add a note — an update, a moderation, a second thought…"
                    className="w-full resize-y border-2 border-ink bg-concrete px-3 py-2 font-mono text-sm outline-none placeholder:text-muted focus:bg-surface focus:ring-2 focus:ring-acid"
                  />
                  <button
                    type="submit"
                    disabled={savingNote || !noteBody.trim()}
                    className="mt-2 border-2 border-ink bg-acid px-3 py-1.5 text-xs font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none disabled:opacity-50"
                  >
                    {savingNote ? 'Saving…' : 'Add note'}
                  </button>
                </form>
                <ul className="space-y-2">
                  {notes.length === 0 && (
                    <li className="text-xs uppercase tracking-wide text-muted">
                      No notes yet.
                    </li>
                  )}
                  {notes.map((n) => (
                    <li
                      key={n.id}
                      className="border-l-2 border-ink pl-3 text-sm leading-relaxed"
                    >
                      {n.body}
                      <span className="ml-2 font-mono text-[0.65rem] uppercase tracking-wide text-muted">
                        {timeAgo(n.created_at)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <p className="mt-6 font-mono text-[0.68rem] uppercase tracking-wide text-muted">
              created {formatDate(narrative.created_at)} · updated {timeAgo(narrative.updated_at)}
            </p>
          </>
        )}
      </main>
    </div>
  )
}

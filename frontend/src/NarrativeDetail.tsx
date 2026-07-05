import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import type { User } from '@supabase/supabase-js'
import { api } from './lib/api'
import { Header } from './Header'
import { Markdown } from './Markdown'
import { QuoteCard } from './QuoteCard'
import { Label } from './ui'
import { formatDateTime, timeAgo } from './lib/time'
import type { Company, Narrative, Note, PricePerformance, Source } from './lib/types'

export function NarrativeDetail({ user }: { user: User }) {
  const { id } = useParams<{ id: string }>()
  const username = user.email?.split('@')[0] ?? 'you'
  const [narrative, setNarrative] = useState<Narrative | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [notes, setNotes] = useState<Note[]>([])
  const [quotes, setQuotes] = useState<Record<string, PricePerformance>>({})
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  const [noteBody, setNoteBody] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [togglingActive, setTogglingActive] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const [n, cos, srcs, nts] = await Promise.all([
          api.get<Narrative>(`/narratives/${id}`),
          api.get<Company[]>(`/narratives/${id}/companies`),
          api.get<Source[]>(`/narratives/${id}/sources`),
          api.get<Note[]>(`/narratives/${id}/notes`),
        ])
        setNarrative(n)
        setCompanies(cos)
        setSources(srcs)
        setNotes(nts)
        const since = n.created_at.slice(0, 10)
        const q = await Promise.all(
          cos.map(async (c) => {
            try {
              return [c.id, await api.get<PricePerformance>(`/prices/${c.ticker}/performance?since=${since}`)] as const
            } catch {
              return [c.id, { ticker: c.ticker, as_of: null, performance: {} }] as const
            }
          }),
        )
        setQuotes(Object.fromEntries(q))
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
      setNarrative(await api.patch<Narrative>(`/narratives/${id}`, { is_active: !narrative.is_active }))
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

  const n = narrative

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header maxW="max-w-5xl" />
      <main className="mx-auto max-w-5xl px-4 py-8">
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

        {n && (
          <div className="mt-4 border-2 border-ink shadow-hard">
            {/* Dark masthead */}
            <div className="bg-ink px-4 py-3">
              <div className="flex items-start justify-between gap-3">
                <h1 className="font-display text-xl font-bold tracking-tight text-surface sm:text-2xl">{n.title}</h1>
                <div className="shrink-0 text-right font-mono text-[0.62rem] uppercase tracking-wide">
                  <div className={n.is_active ? 'text-acid' : 'text-surface/50'}>
                    {n.is_active ? '● Active' : '○ Inactive'}
                  </div>
                  <button
                    onClick={toggleActive}
                    disabled={togglingActive}
                    className="text-[0.6rem] text-surface/60 underline decoration-dotted hover:text-acid disabled:opacity-50"
                  >
                    {n.is_active ? 'retire' : 'reactivate'}
                  </button>
                </div>
              </div>
              <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[0.62rem] uppercase tracking-wide">
                {n.positioning && <span className="bg-acid px-1.5 py-0.5 font-bold text-ink">{n.positioning}</span>}
                {companies.map((c) => (
                  <Link key={c.id} to={`/companies/${c.symbol.toLowerCase()}`} className="text-surface hover:text-acid">
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
              <form onSubmit={addNote}>
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
                  <li className="text-xs uppercase tracking-wide text-muted">No notes yet.</li>
                )}
                {notes.map((note) => (
                  <li key={note.id} className="border-l-2 border-ink pl-3 text-sm leading-relaxed">
                    {note.body}
                    <span className="ml-2 font-mono text-[0.65rem] uppercase tracking-wide text-muted">
                      {timeAgo(note.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

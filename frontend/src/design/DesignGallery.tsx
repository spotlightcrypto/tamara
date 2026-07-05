// TEMPORARY: a gallery to preview four cohesive layout options (A/B/C/D) for the
// narrative page and pick one. When chosen, the winner graduates to the real
// /narratives/:id route and this whole design/ folder is deleted.
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import type { User } from '@supabase/supabase-js'
import { api } from '../lib/api'
import { Header } from '../Header'
import type { Company, Narrative, Note, PricePerformance, Source } from '../lib/types'
import type { DesignData } from './shared'
import { DesignA } from './DesignA'
import { DesignB } from './DesignB'
import { DesignC } from './DesignC'
import { DesignD } from './DesignD'

const OPTIONS = [
  { key: 'A', label: 'Dossier', Comp: DesignA },
  { key: 'B', label: 'Editorial', Comp: DesignB },
  { key: 'C', label: 'Terminal', Comp: DesignC },
  { key: 'D', label: 'Ticker', Comp: DesignD },
] as const

export function DesignGallery({ user }: { user: User }) {
  const { id } = useParams<{ id: string }>()
  const [narrative, setNarrative] = useState<Narrative | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [notes, setNotes] = useState<Note[]>([])
  const [quotes, setQuotes] = useState<Record<string, PricePerformance>>({})
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [sel, setSel] = useState<(typeof OPTIONS)[number]['key']>('A')
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

  async function onAddNote(body: string) {
    const note = await api.post<Note>(`/narratives/${id}/notes`, { body })
    setNotes((prev) => [note, ...prev])
  }

  async function onToggleActive() {
    if (!narrative) return
    setTogglingActive(true)
    try {
      setNarrative(await api.patch<Narrative>(`/narratives/${id}`, { is_active: !narrative.is_active }))
    } finally {
      setTogglingActive(false)
    }
  }

  const Selected = OPTIONS.find((o) => o.key === sel)!.Comp

  const data: DesignData | null = narrative && {
    narrative,
    companies: companies.map((c) => ({ id: c.id, symbol: c.symbol, ticker: c.ticker })),
    sources: sources.map((s) => ({ id: s.id, url: s.url, title: s.title })),
    notes,
    quotes,
    username: user.email?.split('@')[0] ?? 'you',
    onAddNote,
    onToggleActive,
    togglingActive,
  }

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header maxW="max-w-5xl" />

      {/* Sticky switcher */}
      <div className="sticky top-0 z-20 border-b-2 border-ink bg-ink">
        <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-2">
          <span className="mr-1 font-mono text-[0.62rem] font-bold uppercase tracking-widest text-acid">
            Design preview
          </span>
          {OPTIONS.map((o) => (
            <button
              key={o.key}
              onClick={() => setSel(o.key)}
              className={`border-2 px-2.5 py-1 font-mono text-xs font-bold uppercase tracking-wide transition-colors ${
                sel === o.key
                  ? 'border-acid bg-acid text-ink'
                  : 'border-surface bg-ink text-surface hover:bg-surface hover:text-ink'
              }`}
            >
              {o.key} · {o.label}
            </button>
          ))}
          <Link
            to={`/narratives/${id}`}
            className="ml-auto inline-flex items-center gap-1 font-mono text-[0.62rem] font-bold uppercase tracking-wide text-surface hover:text-acid"
          >
            <ArrowLeft size={12} strokeWidth={2.5} /> live page
          </Link>
        </div>
      </div>

      {loading && <p className="mx-auto max-w-5xl px-4 py-10 text-sm uppercase tracking-wide text-muted">Loading…</p>}
      {!loading && notFound && (
        <p className="mx-auto max-w-5xl px-4 py-10 text-sm uppercase tracking-wide text-muted">Narrative not found.</p>
      )}
      {data && <Selected d={data} />}
    </div>
  )
}

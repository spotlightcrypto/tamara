import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, PenLine } from 'lucide-react'
import { api } from './lib/api'
import { Header } from './Header'
import { IntakeModal } from './IntakeModal'
import { NarrativeCard } from './NarrativeCard'
import { EmptyState, Loading } from './ui'
import type { Company, NarrativeWithCompanies, ResolvedListing } from './lib/types'

export function CompanyPage() {
  // The route slug is the canonical ticker:mic, e.g. "crwv:xnas". (Older
  // ticker:exchange-name links still resolve — the backend maps either to a MIC.)
  const { symbol } = useParams<{ symbol: string }>()
  const [company, setCompany] = useState<Company | null>(null)
  const [narratives, setNarratives] = useState<NarrativeWithCompanies[]>([])
  // A listing we don't have locally but resolved externally — offer to start its
  // first narrative rather than showing a dead "not found".
  const [resolved, setResolved] = useState<ResolvedListing | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    ;(async () => {
      const [ticker, mic] = (symbol ?? '').split(':')
      if (!ticker || !mic) {
        setLoading(false)
        return
      }
      try {
        // Resolve the company by its slug parts, then load its narratives by id.
        const c = await api.get<Company>(`/companies/by-symbol/${ticker}/${mic}`)
        setCompany(c)
        setNarratives(await api.get<NarrativeWithCompanies[]>(`/companies/${c.id}/narratives`))
      } catch {
        // Not in our DB yet — try the external resolver so the user can start the
        // first narrative for this ticker instead of hitting a dead end.
        try {
          const hits = await api.get<ResolvedListing[]>(`/companies/resolve?q=${encodeURIComponent(ticker)}`)
          const match =
            hits.find((h) => h.slug === (symbol ?? '').toLowerCase()) ??
            hits.find((h) => h.ticker.toLowerCase() === ticker.toLowerCase()) ??
            null
          if (match) setResolved(match)
        } catch {
          // leave resolved null -> the "not found" branch renders
        }
      } finally {
        setLoading(false)
      }
    })()
  }, [symbol])

  // Pre-seed the intake kernel so the agent picks the ticker up immediately.
  const kernel = resolved
    ? `${resolved.name} ($${resolved.ticker} · ${resolved.exchange}) — `
    : ''

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-8">
       <div className="max-w-3xl">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-muted hover:text-ink"
        >
          <ArrowLeft size={14} strokeWidth={2.5} /> Back
        </Link>

        {/* One resolution point — no partial/flashing states while data loads. */}
        {loading ? (
          <div className="mt-6">
            <Loading />
          </div>
        ) : company ? (
          <>
            <div className="mt-4 border-2 border-ink bg-ink px-4 py-4 shadow-hard">
              <div className="font-mono text-sm font-bold uppercase tracking-widest text-acid">
                {company.symbol}
              </div>
              <h1 className="mt-0.5 font-display text-2xl font-bold tracking-tight text-surface sm:text-3xl">
                {company.name}
              </h1>
              {company.sector && (
                <p className="mt-0.5 font-mono text-xs uppercase tracking-wide text-surface/50">
                  {company.sector}
                </p>
              )}
            </div>

            <h2 className="mt-8 font-display text-xl font-bold uppercase tracking-tight">
              Narratives
            </h2>
            <div className="mt-4 space-y-4">
              {narratives.length === 0 ? (
                <EmptyState>No narratives involve this company yet.</EmptyState>
              ) : (
                narratives.map((n) => <NarrativeCard key={n.id} n={n} />)
              )}
            </div>
          </>
        ) : resolved ? (
          // Known to the market, new to Tamara: invite the first narrative.
          <>
            <div className="mt-4 border-2 border-ink bg-ink px-4 py-4 shadow-hard">
              <div className="font-mono text-sm font-bold uppercase tracking-widest text-acid">
                {resolved.symbol}
              </div>
              <h1 className="mt-0.5 font-display text-2xl font-bold tracking-tight text-surface sm:text-3xl">
                {resolved.name}
              </h1>
              {!resolved.has_price && (
                <p className="mt-0.5 font-mono text-xs uppercase tracking-wide text-surface/50">
                  price coming soon · {resolved.exchange}
                </p>
              )}
            </div>

            <div className="mt-6 border-2 border-ink bg-surface p-5 shadow-hard">
              <p className="font-display text-lg font-bold tracking-tight">
                No one’s written about {resolved.ticker} yet.
              </p>
              <p className="mt-1 text-sm text-muted">
                Be the first — start a narrative and it’ll be attached to this company.
              </p>
              <button
                onClick={() => setCreating(true)}
                className="mt-4 inline-flex items-center gap-1.5 border-2 border-ink bg-acid px-3 py-1.5 text-xs font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none"
              >
                <PenLine size={14} strokeWidth={3} /> Write the first narrative
              </button>
            </div>
          </>
        ) : (
          <div className="mt-6">
            <EmptyState>Company not found.</EmptyState>
          </div>
        )}
       </div>
      </main>

      {creating && <IntakeModal onClose={() => setCreating(false)} initialKernel={kernel} />}
    </div>
  )
}

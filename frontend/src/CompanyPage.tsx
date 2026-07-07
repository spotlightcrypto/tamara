import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from './lib/api'
import { Header } from './Header'
import { NarrativeCard } from './NarrativeCard'
import { EmptyState, Loading } from './ui'
import type { Company, NarrativeWithCompanies } from './lib/types'

export function CompanyPage() {
  // The route slug is the canonical ticker:mic, e.g. "crwv:xnas". (Older
  // ticker:exchange-name links still resolve — the backend maps either to a MIC.)
  const { symbol } = useParams<{ symbol: string }>()
  const [company, setCompany] = useState<Company | null>(null)
  const [narratives, setNarratives] = useState<NarrativeWithCompanies[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    ;(async () => {
      const [ticker, mic] = (symbol ?? '').split(':')
      if (!ticker || !mic) {
        setNotFound(true)
        setLoading(false)
        return
      }
      try {
        // Resolve the company by its slug parts, then load its narratives by id.
        const c = await api.get<Company>(`/companies/by-symbol/${ticker}/${mic}`)
        setCompany(c)
        setNarratives(await api.get<NarrativeWithCompanies[]>(`/companies/${c.id}/narratives`))
      } catch {
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    })()
  }, [symbol])

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
        ) : notFound || !company ? (
          <div className="mt-6">
            <EmptyState>Company not found.</EmptyState>
          </div>
        ) : (
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
        )}
       </div>
      </main>
    </div>
  )
}

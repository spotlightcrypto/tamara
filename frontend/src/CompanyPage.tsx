import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from './lib/api'
import { Header } from './Header'
import { NarrativeCard } from './NarrativeCard'
import type { Company, NarrativeWithCompanies } from './lib/types'

export function CompanyPage() {
  // The route slug is the exchange-qualified symbol, e.g. "crwv:nasdaq".
  const { symbol } = useParams<{ symbol: string }>()
  const [company, setCompany] = useState<Company | null>(null)
  const [narratives, setNarratives] = useState<NarrativeWithCompanies[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    ;(async () => {
      const [ticker, exchange] = (symbol ?? '').split(':')
      if (!ticker || !exchange) {
        setNotFound(true)
        setLoading(false)
        return
      }
      try {
        // Resolve the company by symbol, then load its narratives by id.
        const c = await api.get<Company>(`/companies/by-symbol/${ticker}/${exchange}`)
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
            Company not found.
          </p>
        )}

        {company && (
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
              {narratives.length === 0 && (
                <p className="border-2 border-dashed border-ink p-8 text-center text-sm uppercase tracking-wide text-muted">
                  No narratives involve this company yet.
                </p>
              )}
              {narratives.map((n) => (
                <NarrativeCard key={n.id} n={n} />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

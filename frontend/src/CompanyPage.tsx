import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from './lib/api'
import { Header } from './Header'
import { NarrativeCard } from './NarrativeCard'
import type { Company, NarrativeWithCompanies } from './lib/types'

export function CompanyPage() {
  const { id } = useParams<{ id: string }>()
  const [company, setCompany] = useState<Company | null>(null)
  const [narratives, setNarratives] = useState<NarrativeWithCompanies[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const [c, ns] = await Promise.all([
          api.get<Company>(`/companies/${id}`),
          api.get<NarrativeWithCompanies[]>(`/companies/${id}/narratives`),
        ])
        setCompany(c)
        setNarratives(ns)
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
            <div className="mt-4 border-2 border-ink bg-surface shadow-hard">
              <div className="border-b-2 border-ink bg-acid px-4 py-1.5 font-mono text-sm font-bold uppercase tracking-widest">
                {company.symbol}
              </div>
              <div className="p-4">
                <h1 className="font-display text-3xl font-bold tracking-tight">{company.name}</h1>
                {company.sector && (
                  <p className="mt-1 font-mono text-xs uppercase tracking-wide text-muted">
                    {company.sector}
                  </p>
                )}
              </div>
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

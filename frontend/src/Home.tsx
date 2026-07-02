import { useEffect, useState } from 'react'
import type { User } from '@supabase/supabase-js'
import { api } from './lib/api'
import { Header } from './Header'
import { IntakeWizard } from './IntakeWizard'
import { NarrativeCard } from './NarrativeCard'
import type { Company, Narrative, NarrativeWithCompanies } from './lib/types'

export function Home({ user }: { user: User }) {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const narratives = await api.get<Narrative[]>('/narratives')
      const withCompanies = await Promise.all(
        narratives.map(async (n) => ({
          ...n,
          companies: await api.get<Company[]>(`/narratives/${n.id}/companies`),
        })),
      )
      setItems(withCompanies)
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="font-display text-4xl font-bold uppercase tracking-tight">New narrative</h1>
        <p className="mt-1 text-sm uppercase tracking-wide text-muted">
          // drop in a link, a note, a thesis — Tamara takes it from there
        </p>

        <div className="mt-6">
          <IntakeWizard onCreated={load} />
        </div>

        {error && <p className="mt-4 text-sm text-down">{error}</p>}

        <h2 className="mt-10 font-display text-xl font-bold uppercase tracking-tight">Recent</h2>
        <div className="mt-4 space-y-4">
          {loading && <p className="text-sm uppercase tracking-wide text-muted">Loading…</p>}
          {!loading && items.length === 0 && (
            <p className="border-2 border-dashed border-ink p-8 text-center text-sm uppercase tracking-wide text-muted">
              Nothing yet — drop a kernel above.
            </p>
          )}
          {items.map((n) => (
            <NarrativeCard key={n.id} n={n} creatorEmail={user.email} />
          ))}
        </div>
      </main>
    </div>
  )
}

import { useEffect, useState } from 'react'
import type { User } from '@supabase/supabase-js'
import { api } from './lib/api'
import { Header } from './Header'
import { NarrativeCard } from './NarrativeCard'
import type { NarrativeWithCompanies } from './lib/types'

export function Profile({ user }: { user: User }) {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ;(async () => {
      try {
        setItems(await api.get<NarrativeWithCompanies[]>('/narratives'))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <section className="flex items-center gap-4 border-2 border-ink bg-ink p-4 shadow-hard">
          <div className="grid h-14 w-14 shrink-0 place-items-center border-2 border-acid bg-acid font-display text-2xl font-bold uppercase text-ink">
            {user.email?.[0] ?? '?'}
          </div>
          <div className="min-w-0">
            <div className="font-mono text-sm break-all text-surface">{user.email}</div>
            <div className="mt-0.5 font-mono text-xs uppercase tracking-wide text-surface/50">
              {loading ? '…' : `${items.length} narrative${items.length === 1 ? '' : 's'}`}
            </div>
          </div>
        </section>

        <h2 className="mt-8 font-display text-xl font-bold uppercase tracking-tight">Your narratives</h2>
        <div className="mt-4 space-y-4">
          {loading && <p className="text-sm uppercase tracking-wide text-muted">Loading…</p>}
          {!loading && items.length === 0 && (
            <p className="border-2 border-dashed border-ink p-8 text-center text-sm uppercase tracking-wide text-muted">
              No narratives yet.
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

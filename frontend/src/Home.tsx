import { useEffect, useState } from 'react'
import { api } from './lib/api'
import { Header } from './Header'
import { NarrativeCard } from './NarrativeCard'
import { EmptyState, Loading } from './ui'
import type { NarrativeWithCompanies } from './lib/types'

export function Home() {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ;(async () => {
      try {
        // One request — the backend embeds each narrative's companies.
        setItems(await api.get<NarrativeWithCompanies[]>('/narratives'))
        setError(null)
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* Single-column content, left-aligned in the wider frame (right gutter
            reserved for a future rail). Creation lives in the header's + New. */}
        <div className="max-w-3xl">
          {error && <p className="mb-4 text-sm text-down">{error}</p>}

          <h2 className="font-display text-xl font-bold uppercase tracking-tight">Recent</h2>
          <div className="mt-4 space-y-4">
            {loading ? (
              <Loading />
            ) : items.length === 0 ? (
              <EmptyState>Nothing yet — hit “＋ New” to start a narrative.</EmptyState>
            ) : (
              items.map((n) => <NarrativeCard key={n.id} n={n} />)
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

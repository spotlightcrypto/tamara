import { useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import type { User } from '@supabase/supabase-js'
import { api } from './lib/api'
import { Header } from './Header'
import { IntakeModal } from './IntakeModal'
import { NarrativeCard } from './NarrativeCard'
import type { Company, Narrative, NarrativeWithCompanies } from './lib/types'

export function Home({ user }: { user: User }) {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [kernel, setKernel] = useState('')
  const [modalKernel, setModalKernel] = useState<string | null>(null)
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

  function generate(e: React.FormEvent) {
    e.preventDefault()
    const text = kernel.trim()
    if (text) setModalKernel(text)
  }

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="font-display text-4xl font-bold uppercase tracking-tight">New narrative</h1>
        <p className="mt-1 text-sm uppercase tracking-wide text-muted">
          // drop in a link, a note, a thesis — Tamara takes it from there
        </p>

        <form onSubmit={generate} className="mt-6 border-2 border-ink bg-surface shadow-hard">
          <div className="border-b-2 border-ink bg-acid px-4 py-1.5 text-xs font-bold uppercase tracking-widest">
            Kernel
          </div>
          <div className="p-4">
            <textarea
              value={kernel}
              onChange={(e) => setKernel(e.target.value)}
              rows={5}
              placeholder={
                'Paste a link, a tweet, a filing, a half-formed thought…\n' +
                'Tamara will read it, ask a few sharp questions, and work it into a positioned thesis.'
              }
              className="w-full resize-y border-2 border-ink bg-concrete px-3 py-2.5 font-mono outline-none placeholder:text-muted focus:bg-surface focus:ring-2 focus:ring-acid"
            />
            <button
              type="submit"
              className="mt-3 inline-flex items-center gap-1.5 border-2 border-ink bg-acid px-4 py-2 font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-none"
            >
              Generate <ArrowRight size={16} strokeWidth={2.5} />
            </button>
          </div>
        </form>

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

      {modalKernel !== null && (
        <IntakeModal kernelText={modalKernel} onClose={() => setModalKernel(null)} />
      )}
    </div>
  )
}

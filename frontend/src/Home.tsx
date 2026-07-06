import { useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { api } from './lib/api'
import { Header } from './Header'
import { IntakeModal } from './IntakeModal'
import { NarrativeCard } from './NarrativeCard'
import { EmptyState, Loading } from './ui'
import type { NarrativeWithCompanies } from './lib/types'

export function Home() {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [kernel, setKernel] = useState('')
  const [modalKernel, setModalKernel] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      // One request — the backend embeds each narrative's companies.
      setItems(await api.get<NarrativeWithCompanies[]>('/narratives'))
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
        <form onSubmit={generate} className="border-2 border-ink shadow-hard">
          <div className="bg-ink px-4 py-3">
            <h1 className="font-display text-2xl font-bold uppercase tracking-tight text-surface">
              New narrative
            </h1>
            <p className="mt-0.5 font-mono text-[0.68rem] uppercase tracking-wide text-surface/50">
              // drop in a link, a note, a thesis — Tamara takes it from there
            </p>
          </div>
          <div className="bg-surface p-4">
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
          {loading ? (
            <Loading />
          ) : items.length === 0 ? (
            <EmptyState>Nothing yet — drop a kernel above.</EmptyState>
          ) : (
            items.map((n) => <NarrativeCard key={n.id} n={n} />)
          )}
        </div>
      </main>

      {modalKernel !== null && (
        <IntakeModal kernelText={modalKernel} onClose={() => setModalKernel(null)} />
      )}
    </div>
  )
}

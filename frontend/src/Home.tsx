import { useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import type { User } from '@supabase/supabase-js'
import { api } from './lib/api'
import { Header } from './Header'
import { NarrativeCard } from './NarrativeCard'
import type { Company, Narrative, NarrativeWithCompanies } from './lib/types'

export function Home({ user }: { user: User }) {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [kernel, setKernel] = useState('')
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

  // NOTE: placeholder ingestion. For now the kernel becomes the thesis and the
  // title is derived from its first line. This is replaced by the agentic
  // intake flow (URL fetch + questionnaire + structured synthesis) — see proposal.
  async function create(e: React.FormEvent) {
    e.preventDefault()
    const text = kernel.trim()
    if (!text) return
    const title = (text.split('\n')[0] || 'Untitled').slice(0, 80)
    try {
      const created = await api.post<Narrative>('/narratives', { title, thesis: text })
      setItems([{ ...created, companies: [] }, ...items])
      setKernel('')
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="font-display text-4xl font-bold uppercase tracking-tight">New narrative</h1>
        <p className="mt-1 text-sm uppercase tracking-wide text-muted">
          // drop in a link, a note, a thesis — anything
        </p>

        <form onSubmit={create} className="mt-6 border-2 border-ink bg-surface shadow-hard">
          <div className="border-b-2 border-ink bg-acid px-4 py-1.5 text-xs font-bold uppercase tracking-widest">
            Kernel
          </div>
          <div className="p-4">
            <textarea
              value={kernel}
              onChange={(e) => setKernel(e.target.value)}
              rows={5}
              placeholder={
                'Paste a link, a tweet, a filing, a chart, a half-formed thought…\n' +
                'Tamara will read it, ask a few sharp questions, and work it into a structured thesis.'
              }
              className="w-full resize-y border-2 border-ink bg-concrete px-3 py-2.5 font-mono outline-none placeholder:text-muted focus:bg-surface focus:ring-2 focus:ring-acid"
            />
            <button
              type="submit"
              className="mt-3 inline-flex items-center gap-1.5 border-2 border-ink bg-acid px-4 py-2 font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-none"
            >
              Work it up <ArrowRight size={16} strokeWidth={2.5} />
            </button>
          </div>
        </form>

        {error && (
          <p className="mt-4 border-2 border-down bg-surface px-3 py-2 text-sm font-bold text-down">
            {error}
          </p>
        )}

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

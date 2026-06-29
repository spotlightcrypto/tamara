import { useEffect, useState } from 'react'
import { api } from './lib/api'
import { supabase } from './lib/supabase'
import type { Narrative } from './lib/types'

export function Narratives() {
  const [items, setItems] = useState<Narrative[]>([])
  const [title, setTitle] = useState('')
  const [thesis, setThesis] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      setItems(await api.get<Narrative[]>('/narratives'))
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

  async function create(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    try {
      const created = await api.post<Narrative>('/narratives', { title, thesis })
      setItems([created, ...items])
      setTitle('')
      setThesis('')
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto max-w-3xl px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">Tamara</h1>
          <button
            onClick={() => supabase.auth.signOut()}
            className="text-sm text-zinc-500 hover:text-zinc-900"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wide">Narratives</h2>

        <form onSubmit={create} className="mt-3 space-y-2 rounded-xl border border-zinc-200 bg-white p-4">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="New narrative title…"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 outline-none focus:border-zinc-900"
          />
          <textarea
            value={thesis}
            onChange={(e) => setThesis(e.target.value)}
            placeholder="Thesis (optional)…"
            rows={2}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 outline-none focus:border-zinc-900"
          />
          <button
            type="submit"
            className="rounded-lg bg-zinc-900 text-white px-4 py-2 text-sm font-medium"
          >
            Create narrative
          </button>
        </form>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        <ul className="mt-6 space-y-2">
          {loading && <li className="text-zinc-400">Loading…</li>}
          {!loading && items.length === 0 && (
            <li className="text-zinc-400">No narratives yet — create your first above.</li>
          )}
          {items.map((n) => (
            <li key={n.id} className="rounded-xl border border-zinc-200 bg-white p-4">
              <div className="font-medium">{n.title}</div>
              {n.thesis && <p className="mt-1 text-sm text-zinc-500">{n.thesis}</p>}
            </li>
          ))}
        </ul>
      </main>
    </div>
  )
}

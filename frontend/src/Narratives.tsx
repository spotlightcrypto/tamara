import { useEffect, useState } from 'react'
import { api } from './lib/api'
import { supabase } from './lib/supabase'
import type { Company, Narrative, NarrativeWithCompanies } from './lib/types'

export function Narratives() {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [title, setTitle] = useState('')
  const [thesis, setThesis] = useState('')
  const [companyInput, setCompanyInput] = useState('')
  const [pendingCompanies, setPendingCompanies] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const narratives = await api.get<Narrative[]>('/narratives')
      // For each narrative, also pull its attached companies (fine for small lists).
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

  function addCompany() {
    const value = companyInput.trim().toUpperCase()
    if (!value) return
    if (!value.includes(':') || !value.split(':')[1]) {
      setError('Add an exchange too, e.g. CRWV:NASDAQ')
      return
    }
    setError(null)
    if (!pendingCompanies.includes(value)) {
      setPendingCompanies([...pendingCompanies, value])
    }
    setCompanyInput('')
  }

  async function create(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    try {
      const created = await api.post<Narrative>('/narratives', { title, thesis })
      // Attach each pending company to the new narrative.
      const companies: Company[] = []
      for (const symbol of pendingCompanies) {
        companies.push(
          await api.post<Company>(`/narratives/${created.id}/companies`, { ticker: symbol }),
        )
      }
      setItems([{ ...created, companies }, ...items])
      setTitle('')
      setThesis('')
      setPendingCompanies([])
      setError(null)
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

        <form onSubmit={create} className="mt-3 space-y-3 rounded-xl border border-zinc-200 bg-white p-4">
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

          {/* Companies */}
          <div>
            <label className="text-xs font-medium text-zinc-500">Companies</label>
            <div className="mt-1 flex gap-2">
              <input
                value={companyInput}
                onChange={(e) => setCompanyInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addCompany()
                  }
                }}
                placeholder="CRWV:NASDAQ"
                className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 outline-none focus:border-zinc-900"
              />
              <button
                type="button"
                onClick={addCompany}
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium hover:bg-zinc-50"
              >
                Add
              </button>
            </div>
            {pendingCompanies.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {pendingCompanies.map((sym) => (
                  <span
                    key={sym}
                    className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2.5 py-1 text-sm"
                  >
                    {sym}
                    <button
                      type="button"
                      onClick={() => setPendingCompanies(pendingCompanies.filter((s) => s !== sym))}
                      className="text-zinc-400 hover:text-zinc-900"
                      aria-label={`Remove ${sym}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

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
              {n.companies.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {n.companies.map((c) => (
                    <span
                      key={c.id}
                      className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600"
                    >
                      {c.symbol}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      </main>
    </div>
  )
}

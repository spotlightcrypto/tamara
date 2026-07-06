import { useEffect, useState } from 'react'
import { api } from './lib/api'
import { Header } from './Header'
import { NarrativeCard } from './NarrativeCard'
import { UsernameForm } from './UsernameForm'
import { EmptyState, Loading } from './ui'
import type { Me, NarrativeWithCompanies } from './lib/types'

export function Profile({
  me,
  onUsernameChange,
}: {
  me: Me
  onUsernameChange: (username: string) => void
}) {
  const [items, setItems] = useState<NarrativeWithCompanies[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)

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
        <section className="border-2 border-ink bg-ink shadow-hard">
          <div className="flex items-center gap-4 p-4">
            <div className="grid h-14 w-14 shrink-0 place-items-center border-2 border-acid bg-acid font-display text-2xl font-bold uppercase text-ink">
              {me.username?.[0] ?? '?'}
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-mono text-lg font-bold text-surface">@{me.username}</div>
              <div className="mt-0.5 font-mono text-xs text-surface/50 break-all">
                {me.email} · {loading ? '…' : `${items.length} narrative${items.length === 1 ? '' : 's'}`}
              </div>
            </div>
            <button
              onClick={() => setEditing((v) => !v)}
              className="shrink-0 border-2 border-surface/40 px-2 py-1 font-mono text-[0.62rem] font-bold uppercase tracking-wide text-surface hover:border-acid hover:text-acid"
            >
              {editing ? 'cancel' : 'edit'}
            </button>
          </div>
          {editing && (
            <div className="border-t-2 border-surface/20 bg-surface p-4">
              <div className="mb-2 font-mono text-[0.62rem] font-bold uppercase tracking-widest text-muted">
                Change username
              </div>
              <UsernameForm
                initial={me.username ?? ''}
                submitLabel="Save username"
                onClaimed={(u) => {
                  onUsernameChange(u)
                  setEditing(false)
                }}
              />
            </div>
          )}
        </section>

        <h2 className="mt-8 font-display text-xl font-bold uppercase tracking-tight">Your narratives</h2>
        <div className="mt-4 space-y-4">
          {loading ? (
            <Loading />
          ) : items.length === 0 ? (
            <EmptyState>No narratives yet.</EmptyState>
          ) : (
            items.map((n) => <NarrativeCard key={n.id} n={n} />)
          )}
        </div>
      </main>
    </div>
  )
}

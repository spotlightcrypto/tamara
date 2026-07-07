import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Lock } from 'lucide-react'
import { api } from './lib/api'
import { Logo } from './Logo'
import { Label, EmptyState, Loading } from './ui'
import { formatDate } from './lib/time'
import type { NarrativePreview } from './lib/types'

// Logged-OUT view of a public narrative: title + a short excerpt only, with a
// prompt to sign in for the rest. Authenticated users never land here — App
// routes them to the full NarrativeDetail instead.
export function NarrativePreviewPage() {
  const { id } = useParams<{ id: string }>()
  const [teaser, setTeaser] = useState<NarrativePreview | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ;(async () => {
      try {
        setTeaser(await api.get<NarrativePreview>(`/public/narratives/${id}`))
      } catch {
        setTeaser(null)
      } finally {
        setLoading(false)
      }
    })()
  }, [id])

  return (
    <div className="min-h-screen bg-concrete text-ink">
      <div className="h-1.5 w-full border-b-2 border-ink bg-acid" />
      <header className="border-b-2 border-ink bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-2.5">
          <Link to="/">
            <Logo />
          </Link>
          <Link
            to="/"
            className="border-2 border-ink bg-acid px-2.5 py-1 text-xs font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none"
          >
            Sign in
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        {loading ? (
          <Loading />
        ) : !teaser ? (
          <EmptyState>Narrative not found.</EmptyState>
        ) : (
          <article className="border-2 border-ink shadow-hard">
            <div className="bg-ink px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="font-display text-xl font-bold tracking-tight text-surface sm:text-2xl">
                  {teaser.title}
                </h1>
                {teaser.positioning && <Label>{teaser.positioning}</Label>}
              </div>
              <div className="mt-1.5 font-mono text-[0.62rem] uppercase tracking-wide text-surface/60">
                {teaser.author_username && <span className="text-surface">{teaser.author_username}</span>}
                <span className="text-surface/50"> · {formatDate(teaser.created_at)}</span>
              </div>
            </div>

            <div className="bg-surface p-4">
              {/* The teaser: first ~100 chars, then a hard cut with a sign-in gate. */}
              <p className="leading-relaxed">
                {teaser.preview}
                {teaser.truncated && <span className="text-muted">…</span>}
              </p>

              <div className="mt-5 border-t-2 border-dashed border-ink pt-4">
                <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-muted">
                  <Lock size={14} strokeWidth={2.5} /> The rest is for members
                </div>
                <p className="mt-1 text-sm text-muted">
                  Sign in to read the full narrative, its companies, sources, and notes.
                </p>
                <Link
                  to="/"
                  className="mt-3 inline-flex items-center border-2 border-ink bg-acid px-3 py-1.5 text-xs font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none"
                >
                  Sign in to read more
                </Link>
              </div>
            </div>
          </article>
        )}
      </main>
    </div>
  )
}

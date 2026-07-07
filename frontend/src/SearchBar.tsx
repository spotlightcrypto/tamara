import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { api } from './lib/api'
import type { ResolvedListing, SearchResults } from './lib/types'

// Home-page search: local matches (the caller's narratives + known companies)
// with a debounced /search call, plus an on-demand "search all markets" that
// resolves tickers we don't have locally so the user can start the first
// narrative for them. Selecting any company routes to its page by slug.
export function SearchBar() {
  const [q, setQ] = useState('')
  const [res, setRes] = useState<SearchResults | null>(null)
  const [ext, setExt] = useState<ResolvedListing[] | null>(null)
  const [extLoading, setExtLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const box = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // Debounced local search. Reset any external results when the query changes.
  useEffect(() => {
    const term = q.trim()
    setExt(null)
    if (!term) {
      setRes(null)
      return
    }
    const t = setTimeout(async () => {
      try {
        setRes(await api.get<SearchResults>(`/search?q=${encodeURIComponent(term)}`))
      } catch {
        setRes(null)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [q])

  // Close the dropdown on an outside click.
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [])

  const runExternal = async () => {
    const term = q.trim()
    if (!term) return
    setExtLoading(true)
    try {
      setExt(await api.get<ResolvedListing[]>(`/companies/resolve?q=${encodeURIComponent(term)}`))
    } catch {
      setExt([])
    } finally {
      setExtLoading(false)
    }
  }

  const go = (path: string) => {
    setOpen(false)
    setQ('')
    navigate(path)
  }

  const term = q.trim()
  const hasLocal = res && (res.narratives.length > 0 || res.companies.length > 0)
  const showPanel = open && term.length > 0

  return (
    <div ref={box} className="relative">
      <div className="flex items-center gap-2 border-2 border-ink bg-surface px-2.5 py-1.5 shadow-hard focus-within:bg-acid/10">
        <Search size={16} strokeWidth={2.5} className="shrink-0 text-muted" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => e.key === 'Escape' && setOpen(false)}
          placeholder="Search narratives & companies…"
          className="w-full bg-transparent font-mono text-sm outline-none placeholder:text-muted"
        />
      </div>

      {showPanel && (
        <div className="absolute z-40 mt-1.5 w-full border-2 border-ink bg-surface shadow-hard">
          {res && res.narratives.length > 0 && (
            <Section label="Narratives">
              {res.narratives.map((n) => (
                <Row key={n.id} onClick={() => go(`/narratives/${n.id}`)}>
                  <span className="truncate font-display font-bold">{n.title}</span>
                </Row>
              ))}
            </Section>
          )}

          {res && res.companies.length > 0 && (
            <Section label="Companies">
              {res.companies.map((c) => (
                <Row key={c.id} onClick={() => go(`/companies/${c.slug}`)}>
                  <Tag>{c.symbol}</Tag>
                  <span className="truncate text-muted">{c.name}</span>
                </Row>
              ))}
            </Section>
          )}

          {/* Nothing local, or the user wants to reach beyond their own data. */}
          {ext === null ? (
            <button
              onMouseDown={(e) => e.preventDefault()}
              onClick={runExternal}
              disabled={extLoading}
              className="flex w-full items-center gap-2 border-t-2 border-ink px-3 py-2 text-left font-mono text-xs font-bold uppercase tracking-wide hover:bg-acid disabled:opacity-60"
            >
              <Search size={13} strokeWidth={3} />
              {extLoading ? 'Searching all markets…' : `Search all markets for “${term}”`}
            </button>
          ) : ext.length > 0 ? (
            <Section label="All markets">
              {ext.map((r) => (
                <Row key={r.slug} onClick={() => go(`/companies/${r.slug}`)}>
                  <Tag>{r.symbol}</Tag>
                  <span className="truncate text-muted">{r.name}</span>
                  {!r.has_price && (
                    <span className="ml-auto shrink-0 font-mono text-[0.6rem] uppercase tracking-wide text-muted">
                      no price yet
                    </span>
                  )}
                </Row>
              ))}
            </Section>
          ) : (
            <p className="border-t-2 border-ink px-3 py-2 font-mono text-xs text-muted">
              No listings found for “{term}”.
            </p>
          )}

          {!hasLocal && ext === null && (
            <p className="border-t-2 border-ink px-3 py-2 font-mono text-[0.68rem] text-muted">
              Nothing of yours matches — try all markets to start a new narrative.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-t-2 border-ink first:border-t-0">
      <div className="bg-concrete px-3 py-1 font-mono text-[0.6rem] font-bold uppercase tracking-widest text-muted">
        {label}
      </div>
      {children}
    </div>
  )
}

function Row({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onMouseDown={(e) => e.preventDefault()} // keep focus so the click lands
      onClick={onClick}
      className="flex w-full items-center gap-2 px-3 py-2 text-left font-mono text-sm hover:bg-acid"
    >
      {children}
    </button>
  )
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="shrink-0 border-2 border-ink bg-concrete px-1.5 py-0.5 font-mono text-[0.68rem] font-bold">
      {children}
    </span>
  )
}

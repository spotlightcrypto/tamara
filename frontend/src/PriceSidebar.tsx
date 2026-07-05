import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from './lib/api'
import type { Company, PricePerformance } from './lib/types'

const WINDOWS = ['1D', '1W', '1M', '3M', '6M', '1Y']

// Right-rail quotes for the tickers a narrative is about: price performance over
// standard windows plus the price when the narrative was created, read from our
// cached daily bars.
export function PriceSidebar({
  companies,
  createdAt,
}: {
  companies: Company[]
  createdAt: string
}) {
  const [perf, setPerf] = useState<Record<string, PricePerformance>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const since = createdAt.slice(0, 10) // YYYY-MM-DD
    ;(async () => {
      setLoading(true)
      const entries = await Promise.all(
        companies.map(async (c) => {
          try {
            return [
              c.id,
              await api.get<PricePerformance>(`/prices/${c.ticker}/performance?since=${since}`),
            ] as const
          } catch {
            return [c.id, { ticker: c.ticker, as_of: null, performance: {} }] as const
          }
        }),
      )
      if (!cancelled) {
        setPerf(Object.fromEntries(entries))
        setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [companies, createdAt])

  if (companies.length === 0) return null

  return (
    <aside className="mt-6 shrink-0 lg:mt-0 lg:w-64 lg:sticky lg:top-8">
      <div className="border-2 border-ink bg-surface shadow-hard">
        <div className="border-b-2 border-ink bg-acid px-3 py-1 text-xs font-bold uppercase tracking-widest">
          Quotes
        </div>
        <div className="divide-y-2 divide-ink">
          {companies.map((c) => {
            const p = perf[c.id]
            const asOf = p?.as_of
            return (
              <div key={c.id} className="p-3">
                <Link
                  to={`/companies/${c.id}`}
                  className="inline-block border-2 border-ink bg-concrete px-2 py-0.5 font-mono text-xs font-bold transition-all hover:bg-acid"
                >
                  {c.symbol}
                </Link>
                <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1">
                  {WINDOWS.map((w) => {
                    const v = p?.performance?.[w]
                    const has = typeof v === 'number'
                    return (
                      <div key={w} className="flex items-baseline justify-between font-mono text-xs">
                        <span className="text-muted">{w}</span>
                        <span className={!has ? 'text-muted' : v >= 0 ? 'text-up' : 'text-down'}>
                          {!has ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`}
                        </span>
                      </div>
                    )
                  })}
                </div>
                {typeof p?.since_close === 'number' && (
                  <div className="mt-2 border-t-2 border-ink pt-1.5 font-mono text-xs">
                    <div className="flex items-baseline justify-between">
                      <span className="text-muted">@ created</span>
                      <span>
                        ${p.since_close.toFixed(2)}
                        {typeof p.since_change === 'number' && (
                          <span className={p.since_change >= 0 ? 'text-up' : 'text-down'}>
                            {' '}
                            ({p.since_change >= 0 ? '+' : ''}
                            {p.since_change.toFixed(1)}%)
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                )}
                <div className="mt-1.5 font-mono text-[0.6rem] uppercase tracking-wide text-muted">
                  {loading && !p ? 'loading…' : asOf ? `as of ${asOf}` : 'no price data'}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </aside>
  )
}

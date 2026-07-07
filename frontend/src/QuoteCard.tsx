import { Link } from 'react-router-dom'
import type { PricePerformance } from './lib/types'

const WINDOWS = ['1D', '1W', '1M', '3M', '6M', '1Y']

const fmtPct = (v?: number | null) =>
  typeof v === 'number' ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}%` : '—'
const pctClass = (v?: number | null) =>
  typeof v !== 'number' ? 'text-muted' : v >= 0 ? 'text-up' : 'text-down'

// A quote for one listing: symbol + current price, the six performance windows,
// and the price when the narrative was created. Tier-3 (uncovered) listings have
// no free price source, so we show a "coming soon" note instead of empty windows.
export function QuoteCard({
  company,
  q,
}: {
  company: { id: string; symbol: string; slug: string; tier?: number | null }
  q?: PricePerformance
}) {
  const uncovered = typeof company.tier === 'number' && company.tier >= 3
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <Link
          to={`/companies/${company.slug}`}
          className="border-2 border-ink bg-concrete px-2 py-0.5 font-mono text-xs font-bold transition-all hover:bg-acid"
        >
          {company.symbol}
        </Link>
        {typeof q?.price === 'number' && (
          <span className="font-mono text-sm font-bold tabular-nums">${q.price.toFixed(2)}</span>
        )}
      </div>
      {uncovered ? (
        <p className="mt-1.5 font-mono text-[0.68rem] uppercase tracking-wide text-muted">
          price coming soon
        </p>
      ) : (
        <>
          <div className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-0.5 font-mono text-xs tabular-nums">
            {WINDOWS.map((w) => (
              <div key={w} className="flex items-baseline justify-between">
                <span className="text-muted">{w}</span>
                <span className={pctClass(q?.performance?.[w])}>{fmtPct(q?.performance?.[w])}</span>
              </div>
            ))}
          </div>
          {typeof q?.since_close === 'number' && (
            <div className="mt-1.5 border-t-2 border-ink pt-1 font-mono text-[0.68rem]">
              <span className="text-muted">@created </span>${q.since_close.toFixed(2)}{' '}
              <span className={pctClass(q.since_change)}>({fmtPct(q.since_change)})</span>
            </div>
          )}
        </>
      )}
    </div>
  )
}

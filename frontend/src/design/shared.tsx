// Shared bits for the temporary design-option previews (A/B/C/D). When we pick a
// winner, this + the chosen Design file graduate into the real narrative route
// and the rest get deleted.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Narrative, Note, PricePerformance } from '../lib/types'

export const WINDOWS = ['1D', '1W', '1M', '3M', '6M', '1Y']

export type Quotes = Record<string, PricePerformance>

export const fmtPct = (v?: number | null) =>
  typeof v === 'number' ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}%` : '—'

export const pctClass = (v?: number | null) =>
  typeof v !== 'number' ? 'text-muted' : v >= 0 ? 'text-up' : 'text-down'

// Data every design receives from the gallery container.
export interface DesignData {
  narrative: Narrative
  companies: { id: string; symbol: string; ticker: string }[]
  sources: { id: string; url: string; title: string }[]
  notes: Note[]
  quotes: Quotes
  username: string
  onAddNote: (body: string) => Promise<void>
  onToggleActive: () => Promise<void>
  togglingActive: boolean
}

// A vertical quote card (symbol + the six windows + price at creation). Used by
// the rail-style designs (A/B). Terminal (C) and Ticker (D) render quotes their
// own way.
export function QuoteCard({
  company,
  q,
}: {
  company: { id: string; symbol: string }
  q?: PricePerformance
}) {
  return (
    <div>
      <Link
        to={`/companies/${company.id}`}
        className="inline-block border-2 border-ink bg-concrete px-2 py-0.5 font-mono text-xs font-bold transition-all hover:bg-acid"
      >
        {company.symbol}
      </Link>
      <div className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-0.5 font-mono text-xs">
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
    </div>
  )
}

// A small status control shared across designs (owner-only view via RLS).
export function StatusToggle({
  narrative,
  onToggle,
  busy,
}: {
  narrative: Narrative
  onToggle: () => void
  busy: boolean
}) {
  return (
    <div className="shrink-0 text-right font-mono text-[0.68rem] uppercase tracking-wide">
      <div className={narrative.is_active ? 'text-ink' : 'text-muted'}>
        {narrative.is_active ? '● Active' : '○ Inactive'}
      </div>
      <button
        onClick={onToggle}
        disabled={busy}
        className="mt-0.5 text-[0.62rem] text-muted underline decoration-dotted underline-offset-2 hover:text-ink disabled:opacity-50"
      >
        {narrative.is_active ? 'retire' : 'reactivate'}
      </button>
    </div>
  )
}

// Notes list + add form (logic shared; each design wraps it with its own frame).
export function Notes({
  notes,
  onAdd,
}: {
  notes: Note[]
  onAdd: (body: string) => Promise<void>
}) {
  const [body, setBody] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const b = body.trim()
    if (!b) return
    setSaving(true)
    try {
      await onAdd(b)
      setBody('')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <form onSubmit={submit} className="mb-3">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={2}
          placeholder="Add a note — an update, a moderation, a second thought…"
          className="w-full resize-y border-2 border-ink bg-concrete px-3 py-2 font-mono text-sm outline-none placeholder:text-muted focus:bg-surface focus:ring-2 focus:ring-acid"
        />
        <button
          type="submit"
          disabled={saving || !body.trim()}
          className="mt-2 border-2 border-ink bg-acid px-3 py-1.5 text-xs font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Add note'}
        </button>
      </form>
      <ul className="space-y-2">
        {notes.length === 0 && (
          <li className="text-xs uppercase tracking-wide text-muted">No notes yet.</li>
        )}
        {notes.map((n) => (
          <li key={n.id} className="border-l-2 border-ink pl-3 text-sm leading-relaxed">
            {n.body}
          </li>
        ))}
      </ul>
    </div>
  )
}

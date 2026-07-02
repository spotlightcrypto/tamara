import { useState } from 'react'
import { ArrowRight, Plus, X } from 'lucide-react'
import { api, ApiError } from './lib/api'
import type { Answer, IntakeState, ItemKind, Proposal, Question } from './lib/types'

type Stage = 'kernel' | 'questions' | 'proposal'
const KINDS: ItemKind[] = ['bull', 'bear', 'catalyst', 'risk']

const input =
  'w-full border-2 border-ink bg-concrete px-3 py-2.5 font-mono outline-none ' +
  'placeholder:text-muted focus:bg-surface focus:ring-2 focus:ring-acid'
const acidBtn =
  'inline-flex items-center gap-1.5 border-2 border-ink bg-acid px-4 py-2 font-bold uppercase ' +
  'tracking-wide shadow-hard transition-all hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-none disabled:opacity-50'
const plainBtn =
  'inline-flex items-center gap-1.5 border-2 border-ink bg-surface px-3 py-2 text-sm font-bold uppercase hover:bg-acid'

export function IntakeWizard({ onCreated }: { onCreated: () => void }) {
  const [stage, setStage] = useState<Stage>('kernel')
  const [kernel, setKernel] = useState('')
  const [draftId, setDraftId] = useState<string | null>(null)
  const [round, setRound] = useState(1)
  const [questions, setQuestions] = useState<Question[]>([])
  const [answers, setAnswers] = useState<Record<string, Answer>>({})
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [addCompany, setAddCompany] = useState('')
  const [error, setError] = useState<{ reason?: string; message: string } | null>(null)
  const [loading, setLoading] = useState(false)

  function reset() {
    setStage('kernel'); setKernel(''); setDraftId(null); setQuestions([])
    setAnswers({}); setProposal(null); setError(null)
  }

  function apply(s: IntakeState) {
    setDraftId(s.draft_id)
    setRound(s.round)
    if (s.status === 'proposed' && s.proposal) {
      setProposal(s.proposal)
      setStage('proposal')
    } else {
      setQuestions(s.questions ?? [])
      setAnswers({})
      setStage('questions')
    }
  }

  async function start(e: React.FormEvent) {
    e.preventDefault()
    const text = kernel.trim()
    if (!text) return
    const isUrl = /^https?:\/\/\S+$/i.test(text)
    setLoading(true); setError(null)
    try {
      const s = await api.post<IntakeState>('/narratives/intake', {
        kernel: isUrl ? { kind: 'url', url: text } : { kind: 'text', raw_text: text },
      })
      apply(s)
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) {
        const d = e.detail as { reason?: string; message?: string }
        setError({ reason: d?.reason, message: d?.message ?? "Couldn't read that link." })
      } else setError({ message: (e as Error).message })
    } finally {
      setLoading(false)
    }
  }

  function toggleOption(q: Question, label: string) {
    const cur = answers[q.id]?.selected ?? []
    const next = q.multi_select
      ? cur.includes(label) ? cur.filter((x) => x !== label) : [...cur, label]
      : cur.includes(label) ? [] : [label]
    setAnswers((a) => ({ ...a, [q.id]: { question_id: q.id, selected: next, free_text: a[q.id]?.free_text } }))
  }
  function setFreeText(q: Question, text: string) {
    setAnswers((a) => ({ ...a, [q.id]: { question_id: q.id, selected: a[q.id]?.selected ?? [], free_text: text } }))
  }

  async function submitAnswers(finishNow: boolean) {
    setLoading(true); setError(null)
    const payload = questions.map((q) => answers[q.id] ?? { question_id: q.id, selected: [] })
    try {
      const s = await api.post<IntakeState>(`/narratives/intake/${draftId}/answer`, {
        answers: payload,
        finish_now: finishNow,
      })
      apply(s)
    } catch (e) {
      setError({ message: (e as Error).message })
    } finally {
      setLoading(false)
    }
  }

  async function finalize() {
    if (!proposal) return
    setLoading(true); setError(null)
    try {
      await api.post(`/narratives/intake/${draftId}/finalize`, { proposal })
      reset()
      onCreated()
    } catch (e) {
      setError({ message: (e as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const P = (patch: Partial<Proposal>) => setProposal((p) => (p ? { ...p, ...patch } : p))

  const errorBox = error && (
    <div className="mt-3 border-2 border-down bg-surface p-3 text-sm">
      <p className="font-bold text-down">{error.message}</p>
      {error.reason && (
        <p className="mt-1 text-muted">Paste the content into the box above instead, or try another URL.</p>
      )}
    </div>
  )

  // ---- KERNEL ----
  if (stage === 'kernel') {
    return (
      <form onSubmit={start} className="border-2 border-ink bg-surface shadow-hard">
        <div className="border-b-2 border-ink bg-acid px-4 py-1.5 text-xs font-bold uppercase tracking-widest">
          Kernel
        </div>
        <div className="p-4">
          <textarea
            value={kernel}
            onChange={(e) => setKernel(e.target.value)}
            rows={5}
            placeholder={'Paste a link, a tweet, a filing, a half-formed thought…\nTamara will read it, ask a few sharp questions, and work it into a positioned thesis.'}
            className={`${input} resize-y`}
          />
          <button type="submit" disabled={loading} className={`mt-3 ${acidBtn}`}>
            {loading ? 'Reading…' : 'Work it up'} <ArrowRight size={16} strokeWidth={2.5} />
          </button>
          {errorBox}
        </div>
      </form>
    )
  }

  // ---- QUESTIONS ----
  if (stage === 'questions') {
    return (
      <div className="border-2 border-ink bg-surface shadow-hard">
        <div className="flex items-center justify-between border-b-2 border-ink bg-acid px-4 py-1.5 text-xs font-bold uppercase tracking-widest">
          <span>Sharpen the thesis</span>
          <span>Round {round} / 3</span>
        </div>
        <div className="space-y-5 p-4">
          {questions.map((q) => {
            const sel = answers[q.id]?.selected ?? []
            return (
              <div key={q.id}>
                <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">{q.header}</div>
                <div className="mt-0.5 font-display text-lg font-bold">{q.question}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {q.options.map((o) => (
                    <button
                      key={o.label}
                      type="button"
                      onClick={() => toggleOption(q, o.label)}
                      title={o.description ?? undefined}
                      className={`border-2 border-ink px-2.5 py-1 text-sm font-medium ${
                        sel.includes(o.label) ? 'bg-acid' : 'bg-surface hover:bg-concrete'
                      }`}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>
                {q.allow_free_text && (
                  <input
                    value={answers[q.id]?.free_text ?? ''}
                    onChange={(e) => setFreeText(q, e.target.value)}
                    placeholder="Or in your own words…"
                    className={`${input} mt-2 text-sm`}
                  />
                )}
              </div>
            )
          })}
          {questions.length === 0 && <p className="text-sm text-muted">No more questions — generate the thesis.</p>}
          <div className="flex flex-wrap gap-2 pt-1">
            <button onClick={() => submitAnswers(false)} disabled={loading} className={acidBtn}>
              Continue <ArrowRight size={16} strokeWidth={2.5} />
            </button>
            <button onClick={() => submitAnswers(true)} disabled={loading} className={plainBtn}>
              Skip & generate
            </button>
          </div>
          {loading && <p className="text-sm uppercase tracking-wide text-muted">Thinking…</p>}
          {errorBox}
        </div>
      </div>
    )
  }

  // ---- PROPOSAL ----
  if (!proposal) return null
  return (
    <div className="border-2 border-ink bg-surface shadow-hard">
      <div className="flex items-center justify-between border-b-2 border-ink bg-acid px-4 py-1.5 text-xs font-bold uppercase tracking-widest">
        <span>Review &amp; edit</span>
        <span>confidence: {proposal.confidence}</span>
      </div>
      <div className="space-y-4 p-4">
        <input value={proposal.title} onChange={(e) => P({ title: e.target.value })} className={`${input} font-display text-lg font-bold`} />
        <textarea value={proposal.thesis} onChange={(e) => P({ thesis: e.target.value })} rows={3} className={input} />

        {/* companies */}
        <div>
          <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">Companies</div>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            {proposal.companies.map((c, i) => (
              <span key={`${c.ticker}:${c.exchange}`} className="inline-flex items-center gap-1 border-2 border-ink bg-concrete px-2 py-0.5 font-mono text-sm font-bold">
                {c.ticker}:{c.exchange}
                <button onClick={() => P({ companies: proposal.companies.filter((_, j) => j !== i) })}><X size={12} strokeWidth={3} /></button>
              </span>
            ))}
            <input
              value={addCompany}
              onChange={(e) => setAddCompany(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  const [t, ex] = addCompany.toUpperCase().split(':')
                  if (t && ex) { P({ companies: [...proposal.companies, { ticker: t, exchange: ex }] }); setAddCompany('') }
                }
              }}
              placeholder="ADD TICKER:EXCHANGE"
              className="w-44 border-2 border-ink bg-surface px-2 py-0.5 font-mono text-sm outline-none focus:ring-2 focus:ring-acid"
            />
          </div>
        </div>

        {/* items by section */}
        {KINDS.map((kind) => (
          <div key={kind}>
            <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">{kind}</div>
            <div className="mt-1.5 space-y-1.5">
              {proposal.items.map((it, i) =>
                it.kind === kind ? (
                  <div key={i} className="flex gap-2">
                    <textarea
                      value={it.body}
                      onChange={(e) => P({ items: proposal.items.map((x, j) => (j === i ? { ...x, body: e.target.value } : x)) })}
                      rows={2}
                      className={`${input} text-sm`}
                    />
                    <button onClick={() => P({ items: proposal.items.filter((_, j) => j !== i) })} className="shrink-0 self-start border-2 border-ink px-1.5 py-1 hover:bg-acid">
                      <X size={13} strokeWidth={3} />
                    </button>
                  </div>
                ) : null,
              )}
              <button onClick={() => P({ items: [...proposal.items, { kind, body: '' }] })} className="inline-flex items-center gap-1 text-xs font-bold uppercase text-muted hover:text-ink">
                <Plus size={13} strokeWidth={3} /> add
              </button>
            </div>
          </div>
        ))}

        {/* open questions -> notes */}
        {proposal.open_questions.length > 0 && (
          <div>
            <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">Open questions → notes</div>
            <ul className="mt-1.5 space-y-1">
              {proposal.open_questions.map((q, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted">
                  <button onClick={() => P({ open_questions: proposal.open_questions.filter((_, j) => j !== i) })} className="mt-0.5"><X size={12} strokeWidth={3} /></button>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap gap-2 pt-1">
          <button onClick={finalize} disabled={loading} className={acidBtn}>
            {loading ? 'Creating…' : 'Create narrative'}
          </button>
          <button onClick={reset} className={plainBtn}>Start over</button>
        </div>
        {errorBox}
      </div>
    </div>
  )
}

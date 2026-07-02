import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Plus, X } from 'lucide-react'
import { api, ApiError } from './lib/api'
import type { Answer, IntakeState, ItemKind, Proposal, Question } from './lib/types'

type Stage = 'processing' | 'questions' | 'proposal' | 'error'
const KINDS: ItemKind[] = ['bull', 'bear', 'catalyst', 'risk']

const PROC_MESSAGES: Record<string, string[]> = {
  reading: ['Reading the kernel', 'Pulling signal from noise', 'Framing the position', 'Drafting sharp questions'],
  thinking: ['Taking your answers', 'Sharpening the position', 'Deciding what else to ask'],
  synthesizing: ['Weighing the bull case', 'Stress-testing the bear', 'Resolving tickers', 'Committing to a position'],
}

const acidBtn =
  'inline-flex items-center gap-1.5 border-2 border-ink bg-acid px-4 py-2 font-bold uppercase tracking-wide ' +
  'shadow-hard transition-all hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-none disabled:opacity-50'
const plainBtn =
  'inline-flex items-center gap-1.5 border-2 border-ink bg-surface px-3 py-2 text-sm font-bold uppercase hover:bg-acid disabled:opacity-40'
const autoField =
  'w-full border-2 border-ink bg-concrete px-3 py-2 font-mono outline-none focus:bg-surface focus:ring-2 focus:ring-acid [field-sizing:content]'

export function IntakeModal({ kernelText, onClose }: { kernelText: string; onClose: () => void }) {
  const navigate = useNavigate()
  const [stage, setStage] = useState<Stage>('processing')
  const [phase, setPhase] = useState<'reading' | 'thinking' | 'synthesizing'>('reading')
  const [msgIdx, setMsgIdx] = useState(0)
  const [draftId, setDraftId] = useState<string | null>(null)
  const [round, setRound] = useState(1)
  const [questions, setQuestions] = useState<Question[]>([])
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, Answer>>({})
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [addCompany, setAddCompany] = useState('')
  const [error, setError] = useState<{ reason?: string; message: string } | null>(null)

  // cycle processing messages
  useEffect(() => {
    if (stage !== 'processing') return
    setMsgIdx(0)
    const msgs = PROC_MESSAGES[phase]
    const t = setInterval(() => setMsgIdx((i) => (i + 1) % msgs.length), 1400)
    return () => clearInterval(t)
  }, [stage, phase])

  // kick off intake on mount
  useEffect(() => {
    void start()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function apply(s: IntakeState) {
    setDraftId(s.draft_id)
    setRound(s.round)
    if (s.status === 'proposed' && s.proposal) {
      setProposal(s.proposal)
      setStage('proposal')
    } else {
      setQuestions(s.questions ?? [])
      setStep(0)
      setStage('questions')
    }
  }

  function fail(e: unknown) {
    if (e instanceof ApiError && e.status === 422) {
      const d = e.detail as { reason?: string; message?: string }
      setError({ reason: d?.reason, message: d?.message ?? "Couldn't read that link." })
    } else {
      setError({ message: (e as Error).message })
    }
    setStage('error')
  }

  async function start() {
    setPhase('reading')
    setStage('processing')
    const text = kernelText.trim()
    const isUrl = /^https?:\/\/\S+$/i.test(text)
    try {
      apply(
        await api.post<IntakeState>('/narratives/intake', {
          kernel: isUrl ? { kind: 'url', url: text } : { kind: 'text', raw_text: text },
        }),
      )
    } catch (e) {
      fail(e)
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
    setPhase(finishNow || round >= 3 ? 'synthesizing' : 'thinking')
    setStage('processing')
    const payload = questions.map((q) => answers[q.id] ?? { question_id: q.id, selected: [] })
    try {
      apply(await api.post<IntakeState>(`/narratives/intake/${draftId}/answer`, { answers: payload, finish_now: finishNow }))
      setAnswers({})
    } catch (e) {
      fail(e)
    }
  }

  async function finalize() {
    if (!proposal) return
    setPhase('synthesizing')
    setStage('processing')
    try {
      const { narrative_id } = await api.post<{ narrative_id: string }>(
        `/narratives/intake/${draftId}/finalize`,
        { proposal },
      )
      navigate(`/narratives/${narrative_id}`)
    } catch (e) {
      fail(e)
    }
  }

  const P = (patch: Partial<Proposal>) => setProposal((p) => (p ? { ...p, ...patch } : p))

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4" onMouseDown={onClose}>
      <div
        className="max-h-[88vh] w-full max-w-2xl overflow-y-auto border-2 border-ink bg-surface shadow-hard-lg"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b-2 border-ink bg-acid px-4 py-2">
          <span className="text-xs font-bold uppercase tracking-widest">
            {stage === 'proposal' ? 'Review & edit' : stage === 'questions' ? `Sharpen · round ${round}` : 'New narrative'}
          </span>
          <button onClick={onClose} aria-label="Close" className="hover:opacity-70">
            <X size={18} strokeWidth={2.5} />
          </button>
        </div>

        {/* PROCESSING */}
        {stage === 'processing' && (
          <div className="px-6 py-16 text-center">
            <div className="mx-auto mb-6 h-3 w-56 overflow-hidden border-2 border-ink bg-concrete">
              <div className="h-full w-1/4 bg-acid animate-scan" />
            </div>
            <div className="font-display text-xl font-bold uppercase">
              {PROC_MESSAGES[phase][msgIdx]}
              <span className="animate-blink">_</span>
            </div>
          </div>
        )}

        {/* ERROR */}
        {stage === 'error' && error && (
          <div className="p-6">
            <p className="font-display text-lg font-bold uppercase text-down">{error.message}</p>
            {error.reason && (
              <p className="mt-2 text-sm text-muted">
                Close this and paste the article text into the box instead, or try another URL.
              </p>
            )}
            <button onClick={onClose} className={`mt-4 ${plainBtn}`}>Close</button>
          </div>
        )}

        {/* QUESTIONS — one at a time */}
        {stage === 'questions' && questions.length > 0 && (
          <QuestionStep
            q={questions[step]}
            index={step}
            total={questions.length}
            answer={answers[questions[step].id]}
            onToggle={toggleOption}
            onFreeText={setFreeText}
            onBack={() => setStep((s) => Math.max(0, s - 1))}
            onNext={() => setStep((s) => s + 1)}
            onContinue={() => submitAnswers(false)}
            onSkipAll={() => submitAnswers(true)}
          />
        )}
        {stage === 'questions' && questions.length === 0 && (
          <div className="p-6">
            <p className="text-sm text-muted">No questions — generate the thesis.</p>
            <button onClick={() => submitAnswers(true)} className={`mt-4 ${acidBtn}`}>Generate</button>
          </div>
        )}

        {/* PROPOSAL — editable */}
        {stage === 'proposal' && proposal && (
          <div className="space-y-4 p-4">
            <div className="text-right text-[0.7rem] font-bold uppercase tracking-widest text-muted">
              confidence: {proposal.confidence}
            </div>
            <textarea rows={1} value={proposal.title} onChange={(e) => P({ title: e.target.value })}
              className={`${autoField} font-display text-lg font-bold`} />
            <textarea rows={3} value={proposal.thesis} onChange={(e) => P({ thesis: e.target.value })} className={autoField} />

            <div>
              <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">Companies</div>
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                {proposal.companies.map((c, i) => (
                  <span key={`${c.ticker}:${c.exchange}:${i}`}
                    className="inline-flex items-center gap-1 border-2 border-ink bg-concrete px-2 py-0.5 font-mono text-sm font-bold">
                    {c.ticker}:{c.exchange}
                    <button onClick={() => P({ companies: proposal.companies.filter((_, j) => j !== i) })}>
                      <X size={12} strokeWidth={3} />
                    </button>
                  </span>
                ))}
                <input value={addCompany} onChange={(e) => setAddCompany(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      const [t, ex] = addCompany.toUpperCase().split(':')
                      if (t && ex) { P({ companies: [...proposal.companies, { ticker: t, exchange: ex }] }); setAddCompany('') }
                    }
                  }}
                  placeholder="ADD TICKER:EXCHANGE"
                  className="w-44 border-2 border-ink bg-surface px-2 py-0.5 font-mono text-sm outline-none focus:ring-2 focus:ring-acid" />
              </div>
            </div>

            {KINDS.map((kind) => (
              <div key={kind}>
                <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">{kind}</div>
                <div className="mt-1.5 space-y-1.5">
                  {proposal.items.map((it, i) =>
                    it.kind === kind ? (
                      <div key={i} className="flex gap-2">
                        <textarea rows={2} value={it.body}
                          onChange={(e) => P({ items: proposal.items.map((x, j) => (j === i ? { ...x, body: e.target.value } : x)) })}
                          className={`${autoField} text-sm`} />
                        <button onClick={() => P({ items: proposal.items.filter((_, j) => j !== i) })}
                          className="h-fit shrink-0 border-2 border-ink px-1.5 py-1 hover:bg-acid">
                          <X size={13} strokeWidth={3} />
                        </button>
                      </div>
                    ) : null,
                  )}
                  <button onClick={() => P({ items: [...proposal.items, { kind, body: '' }] })}
                    className="inline-flex items-center gap-1 text-xs font-bold uppercase text-muted hover:text-ink">
                    <Plus size={13} strokeWidth={3} /> add
                  </button>
                </div>
              </div>
            ))}

            {proposal.open_questions.length > 0 && (
              <div>
                <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">Open questions → notes</div>
                <ul className="mt-1.5 space-y-1">
                  {proposal.open_questions.map((q, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-muted">
                      <button onClick={() => P({ open_questions: proposal.open_questions.filter((_, j) => j !== i) })} className="mt-0.5">
                        <X size={12} strokeWidth={3} />
                      </button>
                      <span>{q}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="sticky bottom-0 -mx-4 -mb-4 flex gap-2 border-t-2 border-ink bg-surface px-4 py-3">
              <button onClick={finalize} className={acidBtn}>Create narrative</button>
              <button onClick={onClose} className={plainBtn}>Discard</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function QuestionStep({
  q, index, total, answer, onToggle, onFreeText, onBack, onNext, onContinue, onSkipAll,
}: {
  q: Question
  index: number
  total: number
  answer?: Answer
  onToggle: (q: Question, label: string) => void
  onFreeText: (q: Question, text: string) => void
  onBack: () => void
  onNext: () => void
  onContinue: () => void
  onSkipAll: () => void
}) {
  const sel = answer?.selected ?? []
  const isLast = index === total - 1
  return (
    <div className="p-6">
      {/* step progress dots */}
      <div className="mb-4 flex items-center gap-1.5">
        {Array.from({ length: total }).map((_, i) => (
          <div key={i} className={`h-1.5 flex-1 border border-ink ${i <= index ? 'bg-acid' : 'bg-concrete'}`} />
        ))}
      </div>
      <div className="text-[0.7rem] font-bold uppercase tracking-widest text-muted">
        {q.header} · {index + 1} / {total}
      </div>
      <div className="mt-1 font-display text-2xl font-bold">{q.question}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {q.options.map((o) => (
          <button key={o.label} onClick={() => onToggle(q, o.label)} title={o.description ?? undefined}
            className={`border-2 border-ink px-3 py-1.5 text-sm font-medium ${sel.includes(o.label) ? 'bg-acid' : 'bg-surface hover:bg-concrete'}`}>
            {o.label}
          </button>
        ))}
      </div>
      {q.allow_free_text && (
        <input value={answer?.free_text ?? ''} onChange={(e) => onFreeText(q, e.target.value)} placeholder="Or in your own words…"
          className="mt-3 w-full border-2 border-ink bg-concrete px-3 py-2 font-mono text-sm outline-none focus:bg-surface focus:ring-2 focus:ring-acid" />
      )}
      <div className="mt-6 flex items-center justify-between">
        <button onClick={onBack} disabled={index === 0} className={plainBtn}>
          <ArrowLeft size={15} strokeWidth={2.5} /> Back
        </button>
        <div className="flex gap-2">
          <button onClick={onSkipAll} className={plainBtn}>Skip &amp; generate</button>
          {isLast ? (
            <button onClick={onContinue} className={acidBtn}>Generate <ArrowRight size={16} strokeWidth={2.5} /></button>
          ) : (
            <button onClick={onNext} className={acidBtn}>Next <ArrowRight size={16} strokeWidth={2.5} /></button>
          )}
        </div>
      </div>
    </div>
  )
}

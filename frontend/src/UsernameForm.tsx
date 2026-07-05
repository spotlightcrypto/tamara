import { useEffect, useState } from 'react'
import { api, ApiError } from './lib/api'
import type { Profile, UsernameCheck } from './lib/types'

// Username input with debounced live availability + claim. Reused by the
// first-login setup gate and the profile settings editor.
export function UsernameForm({
  initial = '',
  submitLabel,
  onClaimed,
}: {
  initial?: string
  submitLabel: string
  onClaimed: (username: string) => void
}) {
  const [value, setValue] = useState(initial)
  const [check, setCheck] = useState<UsernameCheck | null>(null)
  const [checking, setChecking] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const v = value.trim().toLowerCase()

  // Debounced availability check.
  useEffect(() => {
    setCheck(null)
    setError(null)
    if (!v) return
    setChecking(true)
    const t = setTimeout(async () => {
      try {
        setCheck(await api.get<UsernameCheck>(`/usernames/check?u=${encodeURIComponent(v)}`))
      } catch {
        setCheck(null)
      } finally {
        setChecking(false)
      }
    }, 350)
    return () => clearTimeout(t)
  }, [v])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!v || !check?.available) return
    setSubmitting(true)
    setError(null)
    try {
      const profile = await api.post<Profile>('/me/username', { username: v })
      onClaimed(profile.username)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const status = !v
    ? null
    : checking
      ? { text: 'checking…', cls: 'text-muted' }
      : check?.available
        ? { text: '✓ available', cls: 'text-up' }
        : check
          ? { text: `✗ ${check.reason ?? 'unavailable'}`, cls: 'text-down' }
          : null

  return (
    <form onSubmit={submit}>
      <div className="flex items-center border-2 border-ink bg-concrete focus-within:bg-surface focus-within:ring-2 focus-within:ring-acid">
        <span className="pl-3 font-mono text-lg font-bold text-muted">@</span>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value.toLowerCase())}
          autoFocus
          maxLength={20}
          placeholder="username"
          className="w-full bg-transparent px-1 py-2.5 font-mono text-lg font-bold lowercase outline-none placeholder:text-muted"
        />
      </div>
      <div className="mt-1.5 h-4 font-mono text-xs">
        {status && <span className={status.cls}>{status.text}</span>}
      </div>
      <button
        type="submit"
        disabled={submitting || !check?.available}
        className="mt-2 w-full border-2 border-ink bg-acid px-3 py-2.5 font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none disabled:opacity-50"
      >
        {submitting ? 'Saving…' : submitLabel}
      </button>
      {error && <p className="mt-2 text-sm text-down">{error}</p>}
    </form>
  )
}

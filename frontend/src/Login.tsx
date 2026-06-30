import { useState } from 'react'
import { supabase } from './lib/supabase'
import { Logo } from './Logo'

const btn =
  'w-full border-2 border-ink bg-acid px-3 py-2.5 font-bold uppercase tracking-wide text-ink ' +
  'shadow-hard transition-all hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-none ' +
  'disabled:opacity-50 disabled:hover:translate-x-0 disabled:hover:translate-y-0 disabled:hover:shadow-hard'

const input =
  'w-full border-2 border-ink bg-concrete px-3 py-2.5 font-mono outline-none ' +
  'placeholder:text-muted focus:bg-surface focus:ring-2 focus:ring-acid'

export function Login() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function sendLink(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin },
    })
    setLoading(false)
    if (error) setError(error.message)
    else setSent(true)
  }

  return (
    <div className="min-h-screen bg-concrete flex items-center justify-center px-4">
      <div className="w-full max-w-sm border-2 border-ink bg-surface shadow-hard-lg">
        <div className="flex items-center justify-between border-b-2 border-ink px-4 py-2">
          <Logo size={24} />
          <span className="font-mono text-[0.7rem] uppercase tracking-widest text-muted">●&nbsp;auth</span>
        </div>

        <div className="p-5">
          {sent ? (
            <div>
              <p className="font-display text-lg font-bold uppercase">Check your email</p>
              <p className="mt-2 text-sm text-muted">
                Sign-in link sent to <span className="text-ink">{email}</span>. Click it to continue.
              </p>
              <button onClick={() => setSent(false)} className="mt-4 text-sm uppercase tracking-wide underline">
                Use a different email
              </button>
            </div>
          ) : (
            <>
              <p className="mb-4 text-sm uppercase tracking-wide text-muted">
                // your investment theses, sharpened
              </p>
              <form onSubmit={sendLink} className="space-y-3">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={input}
                />
                <button type="submit" disabled={loading} className={btn}>
                  {loading ? 'Sending…' : 'Send sign-in link'}
                </button>
              </form>
            </>
          )}
          {error && <p className="mt-3 text-sm text-down">{error}</p>}
        </div>
      </div>
    </div>
  )
}

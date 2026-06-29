import { useState } from 'react'
import { supabase } from './lib/supabase'

/** Magic-link login: enter email -> Supabase emails a one-time sign-in link.
 *  Clicking the link returns to the app with a session (the Supabase client
 *  detects it from the URL), and App's auth listener swaps in the app. */
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
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm text-center">
        <h1 className="text-3xl font-semibold tracking-tight">Tamara</h1>

        {sent ? (
          <>
            <p className="mt-4 text-zinc-700">Check your email</p>
            <p className="mt-1 text-sm text-zinc-500">
              We sent a sign-in link to <span className="font-medium">{email}</span>. Click it
              to continue.
            </p>
            <button
              onClick={() => setSent(false)}
              className="mt-4 text-sm text-zinc-500 hover:text-zinc-900"
            >
              Use a different email
            </button>
          </>
        ) : (
          <form onSubmit={sendLink} className="mt-6 space-y-3 text-left">
            <p className="text-center text-sm text-zinc-500">Sign in with your email</p>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 outline-none focus:border-zinc-900"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-zinc-900 text-white py-2 font-medium disabled:opacity-50"
            >
              {loading ? 'Sending…' : 'Send sign-in link'}
            </button>
          </form>
        )}

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>
    </div>
  )
}

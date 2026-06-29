import { useState } from 'react'
import { supabase } from './lib/supabase'

/** Email one-time-code login. Step 1: enter email -> Supabase emails a code.
 *  Step 2: enter the code -> verify. On success, App's auth listener takes over. */
export function Login() {
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [stage, setStage] = useState<'email' | 'code'>('email')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function sendCode(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    const { error } = await supabase.auth.signInWithOtp({ email })
    setLoading(false)
    if (error) setError(error.message)
    else setStage('code')
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    const { error } = await supabase.auth.verifyOtp({ email, token: code, type: 'email' })
    setLoading(false)
    if (error) setError(error.message)
  }

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-semibold tracking-tight text-center">Tamara</h1>
        <p className="mt-1 mb-6 text-center text-zinc-500 text-sm">
          {stage === 'email' ? 'Sign in with your email' : `Enter the code sent to ${email}`}
        </p>

        {stage === 'email' ? (
          <form onSubmit={sendCode} className="space-y-3">
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
              {loading ? 'Sending…' : 'Send code'}
            </button>
          </form>
        ) : (
          <form onSubmit={verify} className="space-y-3">
            <input
              inputMode="numeric"
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="123456"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 tracking-widest text-center outline-none focus:border-zinc-900"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-zinc-900 text-white py-2 font-medium disabled:opacity-50"
            >
              {loading ? 'Verifying…' : 'Verify'}
            </button>
            <button
              type="button"
              onClick={() => setStage('email')}
              className="w-full text-sm text-zinc-500 hover:text-zinc-900"
            >
              Use a different email
            </button>
          </form>
        )}

        {error && <p className="mt-3 text-sm text-red-600 text-center">{error}</p>}
      </div>
    </div>
  )
}

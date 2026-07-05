import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'
import { api } from './lib/api'
import type { Me } from './lib/types'
import { Login } from './Login'
import { UsernameSetup } from './UsernameSetup'
import { Home } from './Home'
import { Profile } from './Profile'
import { NarrativeDetail } from './NarrativeDetail'
import { CompanyPage } from './CompanyPage'

// Derive a valid suggested username from an email local-part.
function suggestUsername(email: string | undefined): string {
  return (email ?? '').split('@')[0].toLowerCase().replace(/[^a-z0-9_]/g, '').slice(0, 20)
}

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [ready, setReady] = useState(false)
  // undefined = loading me; 'error' = fetch failed; Me = loaded.
  const [me, setMe] = useState<Me | 'error' | undefined>(undefined)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setReady(true)
    })
    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => setSession(s))
    return () => sub.subscription.unsubscribe()
  }, [])

  // Load the caller's profile whenever the signed-in user changes.
  useEffect(() => {
    if (!session) {
      setMe(undefined)
      return
    }
    let cancelled = false
    setMe(undefined)
    api
      .get<Me>('/me/profile')
      .then((m) => !cancelled && setMe(m))
      .catch(() => !cancelled && setMe('error'))
    return () => {
      cancelled = true
    }
  }, [session?.user?.id])

  if (!ready) return null
  if (!session) return <Login />
  if (me === undefined) return null // profile loading

  if (me === 'error') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-concrete px-4 text-center">
        <div>
          <p className="text-sm uppercase tracking-wide text-muted">Couldn't load your profile.</p>
          <button onClick={() => location.reload()} className="mt-3 border-2 border-ink bg-acid px-4 py-2 text-xs font-bold uppercase tracking-wide shadow-hard">
            Retry
          </button>
        </div>
      </div>
    )
  }

  // First-login gate: no username yet -> must claim one before anything else.
  if (!me.username) {
    return (
      <UsernameSetup
        suggested={suggestUsername(session.user.email)}
        onDone={(username) => setMe({ ...me, username })}
      />
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/profile" element={<Profile me={me} onUsernameChange={(u) => setMe({ ...me, username: u })} />} />
        <Route path="/narratives/:id" element={<NarrativeDetail />} />
        <Route path="/companies/:symbol" element={<CompanyPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

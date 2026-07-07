import { useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { LogOut, Plus } from 'lucide-react'
import { supabase } from './lib/supabase'
import { Logo } from './Logo'
import { IntakeModal } from './IntakeModal'
import { SearchBar } from './SearchBar'

const navItem = ({ isActive }: { isActive: boolean }) =>
  `border-2 border-ink px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${
    isActive ? 'bg-acid' : 'bg-surface hover:bg-acid'
  }`

// One app-wide frame width (max-w-5xl) so the header never jumps between pages.
// Single-column pages keep a narrower content column left-aligned inside it.
export function Header({ maxW = 'max-w-5xl' }: { maxW?: string }) {
  const [creating, setCreating] = useState(false)
  // Search lives in the nav globally — except on the home page, where it has its
  // own prominent spot in the body.
  const onHome = useLocation().pathname === '/'

  return (
    <>
      <div className="h-1.5 w-full border-b-2 border-ink bg-acid" />
      <header className="border-b-2 border-ink bg-surface">
        <div className={`mx-auto flex ${maxW} items-center justify-between gap-3 px-4 py-2.5`}>
          <Link to="/" className="shrink-0">
            <Logo />
          </Link>
          {!onHome && (
            <div className="min-w-0 flex-1 max-w-md">
              <SearchBar />
            </div>
          )}
          <nav className="flex shrink-0 items-center gap-2">
            {/* Primary action — create a narrative from anywhere. */}
            <button
              onClick={() => setCreating(true)}
              className="inline-flex items-center gap-1 border-2 border-ink bg-acid px-2.5 py-1 text-xs font-bold uppercase tracking-wide shadow-hard transition-all hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none"
            >
              <Plus size={14} strokeWidth={3} /> New
            </button>
            <NavLink to="/" end className={navItem}>
              Home
            </NavLink>
            <NavLink to="/profile" className={navItem}>
              Profile
            </NavLink>
            <button
              onClick={() => supabase.auth.signOut()}
              className="inline-flex items-center gap-1.5 border-2 border-ink bg-surface px-2.5 py-1 text-xs font-bold uppercase tracking-wide hover:bg-acid"
            >
              <LogOut size={14} strokeWidth={2.5} /> Exit
            </button>
          </nav>
        </div>
      </header>

      {creating && <IntakeModal onClose={() => setCreating(false)} />}
    </>
  )
}

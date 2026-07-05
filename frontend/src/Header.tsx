import { Link, NavLink } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { supabase } from './lib/supabase'
import { Logo } from './Logo'

const navItem = ({ isActive }: { isActive: boolean }) =>
  `border-2 border-ink px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${
    isActive ? 'bg-acid' : 'bg-surface hover:bg-acid'
  }`

// `maxW` should match the page's content container so the logo/nav align with
// it (most pages are max-w-3xl; the narrative page is wider for its sidebar).
export function Header({ maxW = 'max-w-3xl' }: { maxW?: string }) {
  return (
    <>
      <div className="h-1.5 w-full border-b-2 border-ink bg-acid" />
      <header className="border-b-2 border-ink bg-surface">
        <div className={`mx-auto flex ${maxW} items-center justify-between px-4 py-2.5`}>
          <Link to="/">
            <Logo />
          </Link>
          <nav className="flex items-center gap-2">
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
    </>
  )
}

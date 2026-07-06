// Shared Terminal-design primitives, so every surface uses the same visual
// language (small acid tag labels + dark mastheads).

// A small acid section label — replaces the older full-width acid header bars.
export function Label({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block bg-acid px-1.5 py-0.5 font-mono text-[0.6rem] font-bold uppercase tracking-widest text-ink">
      {children}
    </span>
  )
}

// The one loading indicator used app-wide (matches the intake processing bar):
// a little scanning acid bar + a blinking cursor.
export function Loading({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 font-mono text-xs font-bold uppercase tracking-widest text-muted">
      <span className="inline-block h-3 w-8 overflow-hidden border-2 border-ink bg-concrete">
        <span className="block h-full w-1/3 animate-scan bg-acid" />
      </span>
      {label}
      <span className="animate-blink">_</span>
    </div>
  )
}

// The one empty-state box used app-wide. Only render it AFTER loading resolves.
export function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <p className="border-2 border-dashed border-ink p-8 text-center text-sm uppercase tracking-wide text-muted">
      {children}
    </p>
  )
}

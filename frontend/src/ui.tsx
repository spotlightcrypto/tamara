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

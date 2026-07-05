/** Tamara logo (brutalist): a hard black square with an acid "T" + a mono,
 *  uppercase wordmark. No rounding. */
export function Logo({
  withWordmark = true,
  size = 26,
  className = '',
}: {
  withWordmark?: boolean
  size?: number
  className?: string
}) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg width={size} height={size} viewBox="0 0 26 26" aria-hidden="true" className="shrink-0">
        <rect x="1" y="1" width="24" height="24" className="fill-ink" />
        {/* acid T */}
        <rect x="6" y="7" width="14" height="3.4" className="fill-acid" />
        <rect x="11.3" y="7" width="3.4" height="12.6" className="fill-acid" />
      </svg>
      {withWordmark && (
        <span className="font-display text-lg font-bold uppercase tracking-tight text-ink">
          Tamara
        </span>
      )}
    </span>
  )
}

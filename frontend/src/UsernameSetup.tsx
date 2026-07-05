import { UsernameForm } from './UsernameForm'

// Blocking first-login screen: a user must claim a username before using the app.
export function UsernameSetup({
  suggested,
  onDone,
}: {
  suggested: string
  onDone: (username: string) => void
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-concrete px-4">
      <div className="w-full max-w-sm border-2 border-ink shadow-hard-lg">
        <div className="bg-ink px-4 py-3">
          <div className="font-mono text-[0.62rem] font-bold uppercase tracking-widest text-acid">Welcome</div>
          <div className="mt-0.5 font-display text-xl font-bold uppercase text-surface">Pick your username</div>
        </div>
        <div className="bg-surface p-5">
          <p className="mb-4 text-sm leading-relaxed text-muted">
            This is your public handle on Tamara. Your email stays private — people only ever see your username.
          </p>
          <UsernameForm initial={suggested} submitLabel="Claim username" onClaimed={onDone} />
          <p className="mt-3 font-mono text-[0.65rem] uppercase tracking-wide text-muted">
            3–20 chars · letters, numbers, _ · starts with a letter · you can change it later
          </p>
        </div>
      </div>
    </div>
  )
}

import { useRef } from 'react'
import { Bold, Heading1, Heading2, Heading3, Italic, Underline } from 'lucide-react'

// A markdown textarea with a small formatting toolbar: bold, italic, underline
// (as <u>), and h1/h2/h3. Operations act on the current selection / line.
export function MarkdownEditor({
  value,
  onChange,
  rows = 16,
}: {
  value: string
  onChange: (v: string) => void
  rows?: number
}) {
  const ref = useRef<HTMLTextAreaElement>(null)

  // Wrap the current selection in `before`/`after` (bold, italic, underline).
  function surround(before: string, after: string) {
    const ta = ref.current
    if (!ta) return
    const { selectionStart: s, selectionEnd: e } = ta
    const next = value.slice(0, s) + before + value.slice(s, e) + after + value.slice(e)
    onChange(next)
    requestAnimationFrame(() => {
      ta.focus()
      ta.selectionStart = s + before.length
      ta.selectionEnd = e + before.length
    })
  }

  // Set the heading level of the current line (replacing any existing #'s).
  function heading(hashes: string) {
    const ta = ref.current
    if (!ta) return
    const caret = ta.selectionStart
    const lineStart = value.lastIndexOf('\n', caret - 1) + 1
    const nl = value.indexOf('\n', lineStart)
    const lineEnd = nl === -1 ? value.length : nl
    const line = value.slice(lineStart, lineEnd).replace(/^#{1,6}\s*/, '')
    const next = value.slice(0, lineStart) + `${hashes} ` + line + value.slice(lineEnd)
    onChange(next)
    requestAnimationFrame(() => {
      ta.focus()
      const pos = lineStart + hashes.length + 1 + line.length
      ta.selectionStart = ta.selectionEnd = pos
    })
  }

  const btn = 'grid h-8 w-8 place-items-center border-2 border-ink bg-surface hover:bg-acid'
  return (
    <div className="border-2 border-ink">
      <div className="flex flex-wrap items-center gap-1 border-b-2 border-ink bg-concrete p-1.5">
        <button type="button" onClick={() => surround('**', '**')} className={btn} title="Bold">
          <Bold size={14} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => surround('*', '*')} className={btn} title="Italic">
          <Italic size={14} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => surround('<u>', '</u>')} className={btn} title="Underline">
          <Underline size={14} strokeWidth={2.5} />
        </button>
        <div className="mx-0.5 h-6 w-px bg-ink" />
        <button type="button" onClick={() => heading('#')} className={btn} title="Heading 1">
          <Heading1 size={15} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => heading('##')} className={btn} title="Heading 2">
          <Heading2 size={15} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => heading('###')} className={btn} title="Heading 3">
          <Heading3 size={15} strokeWidth={2.5} />
        </button>
      </div>
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="block w-full resize-y bg-concrete px-3 py-2.5 font-mono text-sm leading-relaxed outline-none focus:bg-surface"
      />
    </div>
  )
}

import { useEffect } from 'react'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import { Markdown } from 'tiptap-markdown'
import { Bold, Heading1, Heading2, Heading3, Italic, List, Underline as UnderlineIcon } from 'lucide-react'

// A WYSIWYG editor that shows real formatting (bold text, headings) rather than
// raw markdown asterisks, and stores markdown. The toolbar toggles marks, so
// pressing Bold on already-bold text un-bolds it.
export function MarkdownEditor({
  value,
  onChange,
}: {
  value: string
  onChange: (v: string) => void
}) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
      Underline,
      Markdown.configure({ html: true, transformPastedText: true }),
    ],
    content: value,
    onUpdate: ({ editor }) => onChange(editor.storage.markdown.getMarkdown()),
    editorProps: {
      attributes: {
        class:
          'min-h-40 max-h-[40vh] overflow-y-auto bg-concrete px-3 py-2.5 font-mono text-sm ' +
          'leading-relaxed outline-none focus:bg-surface',
      },
    },
  })

  // When the value changes from OUTSIDE (e.g. a regenerate replaces the doc),
  // push it into the editor. Normal typing round-trips to the same markdown, so
  // this won't fire mid-edit or jump the cursor.
  useEffect(() => {
    if (!editor) return
    if (value !== editor.storage.markdown.getMarkdown()) {
      editor.commands.setContent(value, false)
    }
  }, [value, editor])

  if (!editor) return null

  const btn = (active: boolean) =>
    `grid h-8 w-8 place-items-center border-2 border-ink ${active ? 'bg-acid' : 'bg-surface hover:bg-acid'}`

  return (
    <div
      className="border-2 border-ink [&_h1]:font-display [&_h1]:text-xl [&_h1]:font-bold [&_h1]:uppercase [&_h1]:tracking-tight
                 [&_h2]:font-display [&_h2]:text-lg [&_h2]:font-bold [&_h2]:uppercase [&_h2]:tracking-tight
                 [&_h3]:font-display [&_h3]:text-base [&_h3]:font-bold [&_h3]:uppercase
                 [&_strong]:font-bold [&_em]:italic [&_ul]:mt-1 [&_ul]:list-disc [&_ul]:pl-5 [&_p]:mt-2 [&_:first-child]:mt-0"
    >
      <div className="flex flex-wrap items-center gap-1 border-b-2 border-ink bg-concrete p-1.5">
        <button type="button" onClick={() => editor.chain().focus().toggleBold().run()}
          className={btn(editor.isActive('bold'))} title="Bold">
          <Bold size={14} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => editor.chain().focus().toggleItalic().run()}
          className={btn(editor.isActive('italic'))} title="Italic">
          <Italic size={14} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => editor.chain().focus().toggleUnderline().run()}
          className={btn(editor.isActive('underline'))} title="Underline">
          <UnderlineIcon size={14} strokeWidth={2.5} />
        </button>
        <div className="mx-0.5 h-6 w-px bg-ink" />
        <button type="button" onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={btn(editor.isActive('heading', { level: 1 }))} title="Heading 1">
          <Heading1 size={15} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={btn(editor.isActive('heading', { level: 2 }))} title="Heading 2">
          <Heading2 size={15} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={btn(editor.isActive('heading', { level: 3 }))} title="Heading 3">
          <Heading3 size={15} strokeWidth={2.5} />
        </button>
        <button type="button" onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={btn(editor.isActive('bulletList'))} title="Bullet list">
          <List size={15} strokeWidth={2.5} />
        </button>
      </div>
      <EditorContent editor={editor} />
    </div>
  )
}

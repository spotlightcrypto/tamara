import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import type { Components } from 'react-markdown'

// Brutalist markdown rendering — used to display a narrative's body_md doc.
// rehypeRaw lets inline <u>…</u> (our underline) render, since markdown has no
// native underline.
const components: Components = {
  h1: ({ children }) => (
    <h1 className="mt-6 font-display text-2xl font-bold uppercase tracking-tight first:mt-0">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mt-6 inline-block border-b-2 border-acid font-display text-xl font-bold uppercase tracking-tight first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mt-5 font-display text-base font-bold uppercase tracking-wide first:mt-0">{children}</h3>
  ),
  p: ({ children }) => <p className="mt-2 leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="mt-2 space-y-1.5">{children}</ul>,
  ol: ({ children }) => <ol className="mt-2 list-decimal space-y-1.5 pl-5">{children}</ol>,
  li: ({ children }) => (
    <li className="leading-relaxed">
      <span className="mr-1.5 text-acid">▸</span>
      {children}
    </li>
  ),
  strong: ({ children }) => <strong className="font-bold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="underline decoration-acid decoration-2 hover:bg-acid">
      {children}
    </a>
  ),
}

export function Markdown({ children }: { children: string }) {
  return (
    <div className="text-[0.95rem] text-ink [&_li>ul]:ml-4 [&_li>ul]:mt-1.5">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  )
}
